import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
import time
import math

class BFSLabApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторна робота №1: Пошук в ширину (BFS)")
        self.root.geometry("1280x780")

        # 0: Звичайний, 1: Орграф, 2: Дерево
        self.graph_type = tk.IntVar(value=0)
        # 0: Зростання номерів, 1: Спадання, 2: За годинниковою стрілкою
        self.traversal_order = tk.IntVar(value=0)
        
        self.start_node = tk.StringVar(value="1")
        self.goal_node = tk.StringVar(value="32")
        self.anim_speed = tk.DoubleVar(value=0.15)

        self.nodes = {}  # id: (x, y)
        self.edges = []  # list of (u, v) - для орграфа u -> v
        
        self.setup_ui()
        self.load_preset_graph(0)

    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Полотно для візуалізації графа
        self.canvas = tk.Canvas(main_frame, bg="white", width=920, height=760, relief=tk.SUNKEN, bd=2)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Панель керування
        ctrl_frame = ttk.Frame(main_frame, width=340)
        ctrl_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        # --- Вид графа ---
        lf_type = ttk.LabelFrame(ctrl_frame, text="1. Вид графа (Пресет >= 30 вершин)")
        lf_type.pack(fill=tk.X, pady=4)
        for val, text in [(0, "Звичайний граф (32 верш., 42 ребра)"), 
                          (1, "Орієнтований граф (32 верш., 42 дуги)"), 
                          (2, "Дерево (32 верш., 31 ребро, 6 гілок)")]:
            ttk.Radiobutton(lf_type, text=text, variable=self.graph_type, value=val,
                            command=lambda v=val: self.load_preset_graph(v)).pack(anchor=tk.W, padx=5, pady=2)

        # --- Параметри пошуку ---
        lf_search = ttk.LabelFrame(ctrl_frame, text="2. Параметри пошуку")
        lf_search.pack(fill=tk.X, pady=4)
        
        f_nodes = ttk.Frame(lf_search)
        f_nodes.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(f_nodes, text="Старт:").pack(side=tk.LEFT)
        ttk.Entry(f_nodes, textvariable=self.start_node, width=5).pack(side=tk.LEFT, padx=5)
        ttk.Label(f_nodes, text="Мета:").pack(side=tk.LEFT)
        ttk.Entry(f_nodes, textvariable=self.goal_node, width=5).pack(side=tk.LEFT, padx=5)
        ttk.Button(f_nodes, text="⇄ Реверс", command=self.swap_start_goal).pack(side=tk.LEFT, padx=5)

        ttk.Label(lf_search, text="Порядок обходу суміжних вершин:").pack(anchor=tk.W, padx=5, pady=2)
        for val, text in [(0, "За зростанням номерів (1 -> 32)"),
                          (1, "За спаданням номерів (32 -> 1)"),
                          (2, "Геометрично (за годинниковою стрілкою)")]:
            ttk.Radiobutton(lf_search, text=text, variable=self.traversal_order, value=val).pack(anchor=tk.W, padx=10)

        ttk.Label(lf_search, text="Затримка анімації (сек):").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Scale(lf_search, from_=0.0, to=0.6, variable=self.anim_speed, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=2)

        btn_run = ttk.Button(lf_search, text="▶ ЗАПУСТИТИ ПОШУК В ШИРИНУ", command=self.run_bfs)
        btn_run.pack(fill=tk.X, padx=5, pady=6)
        ttk.Button(lf_search, text="Скинути колір графа", command=self.draw_graph).pack(fill=tk.X, padx=5, pady=2)

        # --- Редагування графа ---
        lf_edit = ttk.LabelFrame(ctrl_frame, text="3. Модифікація графа (Порядок і Розмір)")
        lf_edit.pack(fill=tk.X, pady=4)

        # Додавання/видалення вершини
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
        ttk.Button(f_v_btn, text="+ Додати вершину", command=self.add_vertex).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(f_v_btn, text="- Видалити вершину", command=self.del_vertex).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        ttk.Separator(lf_edit, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=4)

        # Додавання/видалення ребра/дуги
        f_e = ttk.Frame(lf_edit)
        f_e.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(f_e, text="Від (U):").pack(side=tk.LEFT)
        self.ent_e_u = ttk.Entry(f_e, width=5)
        self.ent_e_u.pack(side=tk.LEFT, padx=3)
        ttk.Label(f_e, text="До (V):").pack(side=tk.LEFT)
        self.ent_e_v = ttk.Entry(f_e, width=5)
        self.ent_e_v.pack(side=tk.LEFT, padx=3)

        f_e_btn = ttk.Frame(lf_edit)
        f_e_btn.pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(f_e_btn, text="+ Додати ребро/дугу", command=self.add_edge).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(f_e_btn, text="- Видалити", command=self.del_edge).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        # --- Легенда ---
        lf_leg = ttk.LabelFrame(ctrl_frame, text="Легенда")
        lf_leg.pack(fill=tk.X, pady=4)
        for col, txt in [("#E0E0E0", "Не відвідана вершина"),
                         ("#FFD54F", "У черзі (відкрита)"),
                         ("#64B5F6", "Розкрита (оброблена)"),
                         ("#81C784", "Знайдений найкоротший шлях")]:
            f = ttk.Frame(lf_leg)
            f.pack(anchor=tk.W, padx=5, pady=1)
            tk.Canvas(f, width=14, height=14, bg=col, highlightthickness=1, highlightbackground="black").pack(side=tk.LEFT)
            ttk.Label(f, text=txt).pack(side=tk.LEFT, padx=5)

        self.lbl_info = ttk.Label(ctrl_frame, text="", font=("Arial", 9, "bold"))
        self.lbl_info.pack(pady=5)

    def load_preset_graph(self, g_type):
        # Фіксовані координати 32 вершин (6 явних гілок від центру/лівого краю)
        self.nodes = {
            1: (70, 380),
            # Гілка 1 (верхня)
            2: (190, 90), 8: (330, 60), 14: (470, 60), 20: (610, 60), 26: (750, 80),
            # Гілка 2
            3: (190, 200), 9: (330, 175), 15: (470, 175), 21: (610, 175), 27: (750, 190),
            # Гілка 3
            4: (190, 310), 10: (330, 295), 16: (470, 295), 22: (610, 295), 28: (750, 305),
            # Гілка 4
            5: (190, 440), 11: (330, 440), 17: (470, 440), 23: (610, 440), 29: (750, 430),
            # Гілка 5
            6: (190, 560), 12: (330, 565), 18: (470, 565), 24: (610, 565), 30: (750, 555),
            # Гілка 6 (нижня)
            7: (190, 675), 13: (330, 690), 19: (470, 690), 25: (610, 690), 31: (750, 675),
            # Фінальна вершина збору
            32: (860, 380)
        }

        # Базовий каркас дерева (31 ребро, 6 гілок)
        tree_edges = [
            (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
            (2, 8), (8, 14), (14, 20), (20, 26),
            (3, 9), (9, 15), (15, 21), (21, 27),
            (4, 10), (10, 16), (16, 22), (22, 28),
            (5, 11), (11, 17), (17, 23), (23, 29),
            (6, 12), (12, 18), (18, 24), (24, 30),
            (7, 13), (13, 19), (19, 25), (25, 31),
            (28, 32) # У дереві лише один шлях веде до 32
        ]

        # Додаткові міжгілкові з'єднання для графа та орграфа (ще 11 ребер -> всього 42)
        cross_edges = [
            (26, 32), (27, 32), (29, 32), (30, 32), (31, 32),
            (3, 8), (9, 16), (11, 16), (17, 24), (12, 19), (22, 27)
        ]

        if g_type == 2:  # Дерево
            self.edges = tree_edges
        else:            # Звичайний або Орграф
            self.edges = tree_edges + cross_edges

        self.draw_graph()

    def swap_start_goal(self):
        s, g = self.start_node.get(), self.goal_node.get()
        self.start_node.set(g)
        self.goal_node.set(s)

    def add_vertex(self):
        try:
            vid = int(self.ent_v_id.get())
            x = int(self.ent_v_x.get())
            y = int(self.ent_v_y.get())
            if vid in self.nodes:
                messagebox.showwarning("Увага", f"Вершина {vid} вже існує! Координати оновлено.")
            self.nodes[vid] = (x, y)
            self.draw_graph()
        except ValueError:
            messagebox.showerror("Помилка", "Введіть цілі числа для ID, X та Y.")

    def del_vertex(self):
        try:
            vid = int(self.ent_v_id.get())
            if vid in self.nodes:
                del self.nodes[vid]
                self.edges = [(u, v) for u, v in self.edges if u != vid and v != vid]
                self.draw_graph()
            else:
                messagebox.showerror("Помилка", "Такої вершини не існує.")
        except ValueError:
            messagebox.showerror("Помилка", "Введіть коректний ID вершини.")

    def add_edge(self):
        try:
            u, v = int(self.ent_e_u.get()), int(self.ent_e_v.get())
            if u not in self.nodes or v not in self.nodes or u == v:
                messagebox.showerror("Помилка", "Некоректні вершини!")
                return
            if (u, v) not in self.edges:
                self.edges.append((u, v))
                self.draw_graph()
        except ValueError:
            messagebox.showerror("Помилка", "Введіть числові номери вершин.")

    def del_edge(self):
        try:
            u, v = int(self.ent_e_u.get()), int(self.ent_e_v.get())
            if (u, v) in self.edges:
                self.edges.remove((u, v))
            elif self.graph_type.get() != 1 and (v, u) in self.edges:
                self.edges.remove((v, u))
            self.draw_graph()
        except ValueError:
            messagebox.showerror("Помилка", "Введіть числові номери вершин.")

    def draw_graph(self, node_colors=None, path_edges=None):
        self.canvas.delete("all")
        if node_colors is None:
            node_colors = {}
        if path_edges is None:
            path_edges = set()

        is_directed = (self.graph_type.get() == 1)
        r = 16

        # Малювання ребер/дуг
        for u, v in self.edges:
            if u not in self.nodes or v not in self.nodes:
                continue
            x1, y1 = self.nodes[u]
            x2, y2 = self.nodes[v]
            
            is_path = (u, v) in path_edges or (not is_directed and (v, u) in path_edges)
            color = "#2E7D32" if is_path else "#888888"
            width = 4 if is_path else 1.5

            if is_directed:
                # Відступ для стрілки, щоб не заходила під коло вершини
                angle = math.atan2(y2 - y1, x2 - x1)
                x2_adj = x2 - r * math.cos(angle)
                y2_adj = y2 - r * math.sin(angle)
                self.canvas.create_line(x1, y1, x2_adj, y2_adj, fill=color, width=width, arrow=tk.LAST, arrowshape=(10, 12, 5))
            else:
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)

        # Малювання вершин
        for vid, (x, y) in self.nodes.items():
            fill_col = node_colors.get(vid, "#E0E0E0")
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=fill_col, outline="black", width=1.5)
            self.canvas.create_text(x, y, text=str(vid), font=("Arial", 10, "bold"))

        self.lbl_info.config(text=f"Порядок (вершин): {len(self.nodes)} | Розмір (ребер/дуг): {len(self.edges)}")
        self.root.update()

    def get_neighbors(self, u):
        is_directed = (self.graph_type.get() == 1)
        neighbors = []
        for a, b in self.edges:
            if a == u and b in self.nodes:
                neighbors.append(b)
            elif not is_directed and b == u and a in self.nodes:
                neighbors.append(a)
        
        neighbors = list(set(neighbors))
        order = self.traversal_order.get()
        if order == 0:
            neighbors.sort()
        elif order == 1:
            neighbors.sort(reverse=True)
        elif order == 2:
            # Сортування за кутом (за годинниковою стрілкою)
            ux, uy = self.nodes[u]
            neighbors.sort(key=lambda v: math.atan2(self.nodes[v][1] - uy, self.nodes[v][0] - ux))
        return neighbors

    def run_bfs(self):
        try:
            start = int(self.start_node.get())
            goal = int(self.goal_node.get())
        except ValueError:
            messagebox.showerror("Помилка", "Початкова та цільова вершини мають бути числами!")
            return

        if start not in self.nodes or goal not in self.nodes:
            messagebox.showerror("Помилка", "Заданих вершин немає у графі!")
            return

        # Підготовка алгоритму BFS
        queue = deque([start])
        visited = {start}
        parent = {start: None}
        
        node_colors = {start: "#FFD54F"}
        expanded_nodes = []
        cycles = 0
        found = False

        t_start = time.perf_counter()

        while queue:
            cycles += 1
            curr = queue.popleft()
            expanded_nodes.append(curr)
            node_colors[curr] = "#64B5F6" # Розкрита

            if curr == goal:
                found = True
                break

            for nxt in self.get_neighbors(curr):
                if nxt not in visited:
                    visited.add(nxt)
                    parent[nxt] = curr
                    queue.append(nxt)
                    node_colors[nxt] = "#FFD54F" # У черзі

            delay = self.anim_speed.get()
            if delay > 0:
                self.draw_graph(node_colors)
                time.sleep(delay)

        t_exec_ms = (time.perf_counter() - t_start) * 1000.0
        # Віднімаємо час штучної затримки анімації для чистого часу алгоритму
        pure_algo_time = max(0.001, t_exec_ms - (cycles * self.anim_speed.get() * 1000.0))

        path = []
        path_edges = set()
        if found:
            curr = goal
            while curr is not None:
                path.append(curr)
                p = parent[curr]
                if p is not None:
                    path_edges.add((p, curr))
                curr = p
            path.reverse()
            for v in path:
                node_colors[v] = "#81C784"

        self.draw_graph(node_colors, path_edges)
        self.show_results_window(start, goal, found, path, cycles, expanded_nodes, pure_algo_time)

    def show_results_window(self, start, goal, found, path, cycles, expanded_nodes, exec_time):
        win = tk.Toplevel(self.root)
        win.title("Результати пошуку в ширину (BFS)")
        win.geometry("520x420")

        txt = tk.Text(win, font=("Consolas", 10), wrap=tk.WORD, padx=10, pady=10)
        txt.pack(fill=tk.BOTH, expand=True)

        g_names = ["Звичайний неорієнтований граф", "Орієнтований граф (Орграф)", "Дерево"]
        o_names = ["За зростанням номерів", "За спаданням номерів", "За годинниковою стрілкою"]

        res_str = f"=== ЗВІТ ПРО ВИКОНАННЯ ПОШУКУ В ШИРИНУ ===\n\n"
        res_str += f"Вид графа: {g_names[self.graph_type.get()]}\n"
        res_str += f"Порядок графа (кількість вершин): {len(self.nodes)}\n"
        res_str += f"Розмір графа (кількість ребер/дуг): {len(self.edges)}\n"
        res_str += f"Порядок обходу сусідів: {o_names[self.traversal_order.get()]}\n"
        res_str += f"Напрямок пошуку: {start} ➔ {goal}\n"
        res_str += "-" * 45 + "\n"

        if found:
            res_str += f"СТАТУС: Шлях УСПІШНО знайдено!\n"
            res_str += f"Знайдений шлях ({len(path)-1} переходів):\n  " + " ➔ ".join(map(str, path)) + "\n\n"
        else:
            res_str += f"СТАТУС: Шлях НЕ ЗНАЙДЕНО (цільова вершина недосяжна).\n\n"

        res_str += f"Кількість виконаних циклів (ітерацій): {cycles}\n"
        res_str += f"Кількість розкритих вершин: {len(expanded_nodes)}\n"
        res_str += f"Список розкритих вершин (порядок розкриття):\n  {expanded_nodes}\n\n"
        res_str += f"Чистий час роботи алгоритму: {exec_time:.4f} мс\n"

        txt.insert(tk.END, res_str)
        txt.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = BFSLabApp(root)
    root.mainloop()