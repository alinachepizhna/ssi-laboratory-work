import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
import time
import math

class GraphSearchLab2App:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторна робота №2: Пошук в ширину (BFS) та в глибину (DFS)")
        self.root.geometry("1320x820")

        # 0: Звичайний, 1: Орграф, 2: Дерево
        self.graph_type = tk.IntVar(value=0)
        # 0: Зростання номерів, 1: Спадання, 2: За годинниковою стрілкою
        self.traversal_order = tk.IntVar(value=0)
        # 0: BFS, 1: Класичний DFS (перший шлях), 2: DFS (пошук найкоротшого шляху)
        self.algo_type = tk.IntVar(value=1)

        self.start_node = tk.StringVar(value="1")
        self.goal_node = tk.StringVar(value="32")
        self.anim_speed = tk.DoubleVar(value=0.10)

        self.nodes = {}  # id: (x, y)
        # edges: список кортежів (u, v, is_directed), де is_directed: True (дуга u->v) або False (ребро u-v)
        self.edges = []

        self.setup_ui()
        self.load_preset_graph(0)

    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Полотно для візуалізації графа
        self.canvas = tk.Canvas(main_frame, bg="white", width=920, height=780, relief=tk.SUNKEN, bd=2)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Панель керування
        ctrl_frame = ttk.Frame(main_frame, width=380)
        ctrl_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        # --- 1. Вибір алгоритму ---
        lf_algo = ttk.LabelFrame(ctrl_frame, text="1. Алгоритм пошуку")
        lf_algo.pack(fill=tk.X, pady=3)
        for val, text in [
            (0, "Пошук в ширину (BFS) — черга FIFO"),
            (1, "Пошук в глибину (DFS класичний) — стек LIFO"),
            (2, "Пошук в глибину (DFS — знаходження найкоротшого)")
        ]:
            ttk.Radiobutton(lf_algo, text=text, variable=self.algo_type, value=val).pack(anchor=tk.W, padx=5, pady=1)

        # --- 2. Вид графа ---
        lf_type = ttk.LabelFrame(ctrl_frame, text="2. Базовий вид графа (Пресет >= 30 вершин)")
        lf_type.pack(fill=tk.X, pady=3)
        for val, text in [
            (0, "Звичайний граф (32 верш., 42 ребра)"),
            (1, "Орієнтований граф (32 верш., 42 дуги)"),
            (2, "Дерево (32 верш., 31 ребро, 6 гілок)")
        ]:
            ttk.Radiobutton(lf_type, text=text, variable=self.graph_type, value=val,
                            command=lambda v=val: self.load_preset_graph(v)).pack(anchor=tk.W, padx=5, pady=1)

        # --- 3. Параметри пошуку ---
        lf_search = ttk.LabelFrame(ctrl_frame, text="3. Параметри та запуск пошуку")
        lf_search.pack(fill=tk.X, pady=3)

        f_nodes = ttk.Frame(lf_search)
        f_nodes.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(f_nodes, text="Старт:").pack(side=tk.LEFT)
        ttk.Entry(f_nodes, textvariable=self.start_node, width=5).pack(side=tk.LEFT, padx=4)
        ttk.Label(f_nodes, text="Мета:").pack(side=tk.LEFT)
        ttk.Entry(f_nodes, textvariable=self.goal_node, width=5).pack(side=tk.LEFT, padx=4)
        ttk.Button(f_nodes, text="⇄ Реверс", command=self.swap_start_goal).pack(side=tk.LEFT, padx=4)

        ttk.Label(lf_search, text="Порядок обходу суміжних вершин:").pack(anchor=tk.W, padx=5, pady=1)
        for val, text in [
            (0, "За зростанням номерів (1 -> 32)"),
            (1, "За спаданням номерів (32 -> 1)"),
            (2, "Геометрично (за годинниковою стрілкою)")
        ]:
            ttk.Radiobutton(lf_search, text=text, variable=self.traversal_order, value=val).pack(anchor=tk.W, padx=10)

        ttk.Label(lf_search, text="Затримка покрокової візуалізації (сек):").pack(anchor=tk.W, padx=5, pady=1)
        ttk.Scale(lf_search, from_=0.0, to=0.5, variable=self.anim_speed, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5)

        ttk.Button(lf_search, text="▶ ЗАПУСТИТИ ОБРАНИЙ ПОШУК", command=self.run_selected_search).pack(fill=tk.X, padx=5, pady=4)
        ttk.Button(lf_search, text="⚔ ПОРІВНЯТИ BFS та DFS (однакові умови)", command=self.compare_bfs_dfs).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(lf_search, text="Скинути колір графа", command=self.draw_graph).pack(fill=tk.X, padx=5, pady=2)

        # --- 4. Редагування графа та заміна ребер на дуги ---
        lf_edit = ttk.LabelFrame(ctrl_frame, text="4. Модифікація графа (Вершини, Ребра ⇄ Дуги)")
        lf_edit.pack(fill=tk.X, pady=3)

        f_v = ttk.Frame(lf_edit)
        f_v.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(f_v, text="Вершина №:").grid(row=0, column=0)
        self.ent_v_id = ttk.Entry(f_v, width=4)
        self.ent_v_id.grid(row=0, column=1)
        ttk.Label(f_v, text="X:").grid(row=0, column=2)
        self.ent_v_x = ttk.Entry(f_v, width=4)
        self.ent_v_x.grid(row=0, column=3)
        ttk.Label(f_v, text="Y:").grid(row=0, column=4)
        self.ent_v_y = ttk.Entry(f_v, width=4)
        self.ent_v_y.grid(row=0, column=5)

        f_v_btn = ttk.Frame(lf_edit)
        f_v_btn.pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(f_v_btn, text="+ Додати верш.", command=self.add_vertex).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(f_v_btn, text="- Видалити верш.", command=self.del_vertex).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        ttk.Separator(lf_edit, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=3)

        f_e = ttk.Frame(lf_edit)
        f_e.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(f_e, text="Від (U):").pack(side=tk.LEFT)
        self.ent_e_u = ttk.Entry(f_e, width=5)
        self.ent_e_u.pack(side=tk.LEFT, padx=3)
        ttk.Label(f_e, text="До (V):").pack(side=tk.LEFT)
        self.ent_e_v = ttk.Entry(f_e, width=5)
        self.ent_e_v.pack(side=tk.LEFT, padx=3)

        f_e_btn1 = ttk.Frame(lf_edit)
        f_e_btn1.pack(fill=tk.X, padx=5, pady=1)
        ttk.Button(f_e_btn1, text="+ Ребро (U—V)", command=lambda: self.add_connection(False)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(f_e_btn1, text="+ Дуга (U➔V)", command=lambda: self.add_connection(True)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        f_e_btn2 = ttk.Frame(lf_edit)
        f_e_btn2.pack(fill=tk.X, padx=5, pady=1)
        ttk.Button(f_e_btn2, text="⇄ Ребро в Дугу (і навпаки)", command=self.toggle_edge_direction).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(f_e_btn2, text="- Видалити зв'язок", command=self.del_connection).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        # --- Легенда ---
        lf_leg = ttk.LabelFrame(ctrl_frame, text="Легенда")
        lf_leg.pack(fill=tk.X, pady=3)
        for col, txt in [
            ("#E0E0E0", "Не відвідана вершина"),
            ("#FFD54F", "У черзі / стеку (відкрита)"),
            ("#64B5F6", "Розкрита (оброблена)"),
            ("#81C784", "Результуючий шлях")
        ]:
            f = ttk.Frame(lf_leg)
            f.pack(anchor=tk.W, padx=5, pady=1)
            tk.Canvas(f, width=14, height=14, bg=col, highlightthickness=1, highlightbackground="black").pack(side=tk.LEFT)
            ttk.Label(f, text=txt).pack(side=tk.LEFT, padx=5)

        self.lbl_info = ttk.Label(ctrl_frame, text="", font=("Arial", 9, "bold"))
        self.lbl_info.pack(pady=4)

    def load_preset_graph(self, g_type):
        self.nodes = {
            1: (70, 380),
            2: (190, 90), 8: (330, 60), 14: (470, 60), 20: (610, 60), 26: (750, 80),
            3: (190, 200), 9: (330, 175), 15: (470, 175), 21: (610, 175), 27: (750, 190),
            4: (190, 310), 10: (330, 295), 16: (470, 295), 22: (610, 295), 28: (750, 305),
            5: (190, 440), 11: (330, 440), 17: (470, 440), 23: (610, 440), 29: (750, 430),
            6: (190, 560), 12: (330, 565), 18: (470, 565), 24: (610, 565), 30: (750, 555),
            7: (190, 675), 13: (330, 690), 19: (470, 690), 25: (610, 690), 31: (750, 675),
            32: (860, 380)
        }

        tree_pairs = [
            (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
            (2, 8), (8, 14), (14, 20), (20, 26),
            (3, 9), (9, 15), (15, 21), (21, 27),
            (4, 10), (10, 16), (16, 22), (22, 28),
            (5, 11), (11, 17), (17, 23), (23, 29),
            (6, 12), (12, 18), (18, 24), (24, 30),
            (7, 13), (13, 19), (19, 25), (25, 31),
            (28, 32)
        ]

        cross_pairs = [
            (26, 32), (27, 32), (29, 32), (30, 32), (31, 32),
            (3, 8), (9, 16), (11, 16), (17, 24), (12, 19), (22, 27)
        ]

        is_dir = (g_type == 1)
        raw = tree_pairs if g_type == 2 else (tree_pairs + cross_pairs)
        self.edges = [(u, v, is_dir) for u, v in raw]
        self.draw_graph()

    def swap_start_goal(self):
        s, g = self.start_node.get(), self.goal_node.get()
        self.start_node.set(g)
        self.goal_node.set(s)

    def add_vertex(self):
        try:
            vid, x, y = int(self.ent_v_id.get()), int(self.ent_v_x.get()), int(self.ent_v_y.get())
            self.nodes[vid] = (x, y)
            self.draw_graph()
        except ValueError:
            messagebox.showerror("Помилка", "Введіть цілі числа для ID, X та Y.")

    def del_vertex(self):
        try:
            vid = int(self.ent_v_id.get())
            if vid in self.nodes:
                del self.nodes[vid]
                self.edges = [(u, v, d) for u, v, d in self.edges if u != vid and v != vid]
                self.draw_graph()
        except ValueError:
            messagebox.showerror("Помилка", "Введіть коректний ID вершини.")

    def add_connection(self, is_directed):
        try:
            u, v = int(self.ent_e_u.get()), int(self.ent_e_v.get())
            if u not in self.nodes or v not in self.nodes or u == v:
                messagebox.showerror("Помилка", "Некоректні вершини!")
                return
            self.del_connection(silent=True)
            self.edges.append((u, v, is_directed))
            self.draw_graph()
        except ValueError:
            messagebox.showerror("Помилка", "Введіть числові номери вершин.")

    def toggle_edge_direction(self):
        try:
            u, v = int(self.ent_e_u.get()), int(self.ent_e_v.get())
            for i, (a, b, d) in enumerate(self.edges):
                if (a == u and b == v) or (a == v and b == u):
                    # Якщо було ребром -> стає дугою u->v; якщо було дугою -> стає ребром
                    self.edges[i] = (u, v, not d)
                    self.draw_graph()
                    return
            messagebox.showwarning("Увага", "Зв'язок між цими вершинами не знайдено.")
        except ValueError:
            messagebox.showerror("Помилка", "Введіть числові номери вершин.")

    def del_connection(self, silent=False):
        try:
            u, v = int(self.ent_e_u.get()), int(self.ent_e_v.get())
            self.edges = [(a, b, d) for a, b, d in self.edges
                          if not ((a == u and b == v) or (not d and a == v and b == u))]
            self.draw_graph()
        except ValueError:
            if not silent:
                messagebox.showerror("Помилка", "Введіть числові номери вершин.")

    def draw_graph(self, node_colors=None, path_edges=None):
        self.canvas.delete("all")
        if node_colors is None:
            node_colors = {}
        if path_edges is None:
            path_edges = set()

        r = 16
        for u, v, is_dir in self.edges:
            if u not in self.nodes or v not in self.nodes:
                continue
            x1, y1 = self.nodes[u]
            x2, y2 = self.nodes[v]

            is_path = (u, v) in path_edges or (not is_dir and (v, u) in path_edges)
            color = "#2E7D32" if is_path else ("#D32F2F" if is_dir else "#888888")
            width = 4 if is_path else 1.6

            if is_dir:
                angle = math.atan2(y2 - y1, x2 - x1)
                x2_adj = x2 - r * math.cos(angle)
                y2_adj = y2 - r * math.sin(angle)
                self.canvas.create_line(x1, y1, x2_adj, y2_adj, fill=color, width=width,
                                        arrow=tk.LAST, arrowshape=(10, 12, 5))
            else:
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)

        for vid, (x, y) in self.nodes.items():
            fill_col = node_colors.get(vid, "#E0E0E0")
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=fill_col, outline="black", width=1.5)
            self.canvas.create_text(x, y, text=str(vid), font=("Arial", 10, "bold"))

        dir_count = sum(1 for _, _, d in self.edges if d)
        undir_count = len(self.edges) - dir_count
        self.lbl_info.config(text=f"Порядок (вершин): {len(self.nodes)} | Ребер: {undir_count} | Дуг: {dir_count}")
        self.root.update()

    def get_neighbors(self, u):
        neighbors = []
        for a, b, is_dir in self.edges:
            if a == u and b in self.nodes:
                neighbors.append(b)
            elif not is_dir and b == u and a in self.nodes:
                neighbors.append(a)

        neighbors = list(set(neighbors))
        order = self.traversal_order.get()
        if order == 0:
            neighbors.sort()
        elif order == 1:
            neighbors.sort(reverse=True)
        elif order == 2:
            ux, uy = self.nodes[u]
            neighbors.sort(key=lambda v: math.atan2(self.nodes[v][1] - uy, self.nodes[v][0] - ux))
        return neighbors

    def execute_bfs(self, start, goal, animate=True):
        queue = deque([start])
        visited = {start}
        parent = {start: None}
        node_colors = {start: "#FFD54F"}
        expanded = []
        cycles = 0
        found = False

        t0 = time.perf_counter()
        while queue:
            cycles += 1
            curr = queue.popleft()
            expanded.append(curr)
            node_colors[curr] = "#64B5F6"

            if curr == goal:
                found = True
                break

            for nxt in self.get_neighbors(curr):
                if nxt not in visited:
                    visited.add(nxt)
                    parent[nxt] = curr
                    queue.append(nxt)
                    node_colors[nxt] = "#FFD54F"

            if animate and self.anim_speed.get() > 0:
                self.draw_graph(node_colors)
                time.sleep(self.anim_speed.get())

        dt = max(0.001, (time.perf_counter() - t0) * 1000.0 - (cycles * self.anim_speed.get() * 1000.0 if animate else 0))
        path = []
        if found:
            c = goal
            while c is not None:
                path.append(c)
                c = parent[c]
            path.reverse()
        return found, path, cycles, expanded, dt, node_colors

    def execute_dfs_classic(self, start, goal, animate=True):
        # Стек зберігає кортежі (вершина, шлях_до_неї)
        stack = [(start, [start])]
        visited = set()
        node_colors = {start: "#FFD54F"}
        expanded = []
        cycles = 0
        found_path = []

        t0 = time.perf_counter()
        while stack:
            cycles += 1
            curr, path = stack.pop()
            if curr in visited:
                continue
            visited.add(curr)
            expanded.append(curr)
            node_colors[curr] = "#64B5F6"

            if curr == goal:
                found_path = path
                break

            # Щоб стек (LIFO) діставав вершини у вибраному порядку, додаємо їх у зворотному порядку
            neighbors = self.get_neighbors(curr)
            for nxt in reversed(neighbors):
                if nxt not in visited:
                    stack.append((nxt, path + [nxt]))
                    node_colors[nxt] = "#FFD54F"

            if animate and self.anim_speed.get() > 0:
                self.draw_graph(node_colors)
                time.sleep(self.anim_speed.get())

        dt = max(0.001, (time.perf_counter() - t0) * 1000.0 - (cycles * self.anim_speed.get() * 1000.0 if animate else 0))
        return bool(found_path), found_path, cycles, expanded, dt, node_colors

    def execute_dfs_shortest(self, start, goal, animate=True):
        # Пошук у глибину з відкатами (Branch & Bound DFS) для гарантованого знаходження найкоротшого шляху
        stack = [(start, [start])]
        best_dist = {start: 0}
        best_path = []
        node_colors = {start: "#FFD54F"}
        expanded = []
        cycles = 0

        t0 = time.perf_counter()
        while stack:
            cycles += 1
            curr, path = stack.pop()

            # Відсікання завідомо довших гілок
            if best_path and len(path) >= len(best_path):
                continue

            if curr not in expanded:
                expanded.append(curr)
            node_colors[curr] = "#64B5F6"

            if curr == goal:
                best_path = path
                continue

            neighbors = self.get_neighbors(curr)
            for nxt in reversed(neighbors):
                if nxt not in path:
                    new_len = len(path)
                    if nxt not in best_dist or new_len < best_dist[nxt]:
                        best_dist[nxt] = new_len
                        stack.append((nxt, path + [nxt]))
                        node_colors[nxt] = "#FFD54F"

            if animate and self.anim_speed.get() > 0:
                self.draw_graph(node_colors)
                time.sleep(self.anim_speed.get())

        dt = max(0.001, (time.perf_counter() - t0) * 1000.0 - (cycles * self.anim_speed.get() * 1000.0 if animate else 0))
        return bool(best_path), best_path, cycles, expanded, dt, node_colors

    def run_selected_search(self):
        try:
            start, goal = int(self.start_node.get()), int(self.goal_node.get())
        except ValueError:
            messagebox.showerror("Помилка", "Старт та Мета мають бути цілими числами!")
            return

        if start not in self.nodes or goal not in self.nodes:
            messagebox.showerror("Помилка", "Заданих вершин немає у графі!")
            return

        algo = self.algo_type.get()
        if algo == 0:
            found, path, cycles, expanded, dt, colors = self.execute_bfs(start, goal, True)
            title = "Пошук в ширину (BFS)"
        elif algo == 1:
            found, path, cycles, expanded, dt, colors = self.execute_dfs_classic(start, goal, True)
            title = "Пошук в глибину (DFS класичний)"
        else:
            found, path, cycles, expanded, dt, colors = self.execute_dfs_shortest(start, goal, True)
            title = "Пошук в глибину (DFS — найкоротший шлях)"

        path_edges = set()
        if found:
            for i in range(len(path) - 1):
                path_edges.add((path[i], path[i + 1]))
            for v in path:
                colors[v] = "#81C784"

        self.draw_graph(colors, path_edges)
        self.show_single_report(title, start, goal, found, path, cycles, expanded, dt)

    def compare_bfs_dfs(self):
        try:
            start, goal = int(self.start_node.get()), int(self.goal_node.get())
        except ValueError:
            return
        if start not in self.nodes or goal not in self.nodes:
            return

        res_bfs = self.execute_bfs(start, goal, animate=False)
        res_dfs1 = self.execute_dfs_classic(start, goal, animate=False)
        res_dfs2 = self.execute_dfs_shortest(start, goal, animate=False)

        win = tk.Toplevel(self.root)
        win.title("Порівняння результатів BFS та DFS за однакових умов")
        win.geometry("680x520")

        txt = tk.Text(win, font=("Consolas", 10), wrap=tk.WORD, padx=10, pady=10)
        txt.pack(fill=tk.BOTH, expand=True)

        o_names = ["За зростанням номерів", "За спаданням номерів", "За годинниковою стрілкою"]
        out = f"=== ПОРІВНЯЛЬНИЙ ЗВІТ: BFS проти DFS ===\n"
        out += f"Порядок графа: {len(self.nodes)} вершин | Розмір: {len(self.edges)} зв'язків\n"
        out += f"Напрямок: {start} ➔ {goal} | Обхід сусідів: {o_names[self.traversal_order.get()]}\n"
        out += "=" * 62 + "\n\n"

        for name, (found, path, cycles, exp, dt, _) in [
            ("1. ПОШУК В ШИРИНУ (BFS)", res_bfs),
            ("2. ПОШУК В ГЛИБИНУ (DFS Класичний — перший знайдений)", res_dfs1),
            ("3. ПОШУК В ГЛИБИНУ (DFS з відкатами — найкоротший)", res_dfs2)
        ]:
            out += f"▶ {name}:\n"
            if found:
                out += f"  • Знайдений шлях ({len(path)-1} переходів): {' ➔ '.join(map(str, path))}\n"
            else:
                out += f"  • Шлях НЕ ЗНАЙДЕНО\n"
            out += f"  • Кількість циклів: {cycles} | Розкрито вершин: {len(exp)}\n"
            out += f"  • Порядок розкриття: {exp}\n"
            out += f"  • Час виконання: {dt:.4f} мс\n"
            out += "-" * 62 + "\n"

        txt.insert(tk.END, out)
        txt.config(state=tk.DISABLED)

    def show_single_report(self, title, start, goal, found, path, cycles, expanded, dt):
        win = tk.Toplevel(self.root)
        win.title(f"Результати: {title}")
        win.geometry("540x430")

        txt = tk.Text(win, font=("Consolas", 10), wrap=tk.WORD, padx=10, pady=10)
        txt.pack(fill=tk.BOTH, expand=True)

        o_names = ["За зростанням номерів", "За спаданням номерів", "За годинниковою стрілкою"]
        res = f"=== ЗВІТ: {title.upper()} ===\n\n"
        res += f"Порядок графа (вершин): {len(self.nodes)} | Розмір (зв'язків): {len(self.edges)}\n"
        res += f"Порядок обходу сусідів: {o_names[self.traversal_order.get()]}\n"
        res += f"Напрямок пошуку: {start} ➔ {goal}\n"
        res += "-" * 50 + "\n"
        if found:
            res += f"СТАТУС: Шлях УСПІШНО знайдено!\n"
            res += f"Довжина шляху: {len(path)-1} ребер/дуг\n"
            res += f"Маршрут: {' ➔ '.join(map(str, path))}\n\n"
        else:
            res += f"СТАТУС: Шлях НЕ ЗНАЙДЕНО.\n\n"
        res += f"Кількість виконаних циклів: {cycles}\n"
        res += f"Кількість розкритих вершин: {len(expanded)}\n"
        res += f"Список розкритих вершин:\n  {expanded}\n\n"
        res += f"Чистий час роботи алгоритму: {dt:.4f} мс\n"

        txt.insert(tk.END, res)
        txt.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = GraphSearchLab2App(root)
    root.mainloop()