import tkinter as tk
from tkinter import ttk, messagebox
import heapq
import time
import math

class DijkstraUkraineApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторна робота: Алгоритм Дейкстри (Автомобільні шляхи України)")
        self.root.geometry("1340x830")

        self.start_city = tk.StringVar(value="Ужгород")
        self.goal_city = tk.StringVar(value="Луганськ")
        self.anim_speed = tk.DoubleVar(value=0.15)
        self.is_directed = tk.BooleanVar(value=False)

        self.nodes = {}  # Назва міста: (x, y)
        self.edges = []  # Список кортежів (місто_1, місто_2, вага_км, чи_орієнтоване)

        self.setup_ui()
        self.load_ukraine_graph()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Полотно для карти автомобільних шляхів України
        self.canvas = tk.Canvas(main_frame, bg="#F8FAFC", width=930, height=800, relief=tk.SUNKEN, bd=2)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Панель керування
        ctrl = ttk.Frame(main_frame, width=390)
        ctrl.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        # --- 1. Вибір маршруту та запуск ---
        lf_search = ttk.LabelFrame(ctrl, text="1. Параметри пошуку маршруту (Алгоритм Дейкстри)")
        lf_search.pack(fill=tk.X, pady=4)

        f_st = ttk.Frame(lf_search)
        f_st.pack(fill=tk.X, padx=5, pady=3)
        ttk.Label(f_st, text="Відправне місто:", width=16).pack(side=tk.LEFT)
        self.cb_start = ttk.Combobox(f_st, textvariable=self.start_city, state="readonly", width=20)
        self.cb_start.pack(side=tk.LEFT, padx=3)

        f_gl = ttk.Frame(lf_search)
        f_gl.pack(fill=tk.X, padx=5, pady=3)
        ttk.Label(f_gl, text="Цільове місто:", width=16).pack(side=tk.LEFT)
        self.cb_goal = ttk.Combobox(f_gl, textvariable=self.goal_city, state="readonly", width=20)
        self.cb_goal.pack(side=tk.LEFT, padx=3)

        ttk.Button(lf_search, text="⇄ Поміняти місцями відправну і цільову точки", command=self.swap_cities).pack(fill=tk.X, padx=5, pady=3)

        ttk.Label(lf_search, text="Затримка покрокової візуалізації (сек):").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Scale(lf_search, from_=0.0, to=0.5, variable=self.anim_speed, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5)

        ttk.Button(lf_search, text="▶ ЗНАЙТИ НАЙКОРОТШИЙ ШЛЯХ (ДЕЙКСТРА)", command=self.run_dijkstra).pack(fill=tk.X, padx=5, pady=6)
        ttk.Button(lf_search, text="⚔ Порівняти з BFS (за кількістю міст vs за км)", command=self.compare_dijkstra_vs_bfs).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(lf_search, text="Скинути візуалізацію пошуку", command=self.draw_graph).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(lf_search, text="↺ Відновити початкову карту України (Табл. 1)", command=self.load_ukraine_graph).pack(fill=tk.X, padx=5, pady=4)

        # --- 2. Модифікація порядку графа (Міста / Вершини) ---
        lf_nodes = ttk.LabelFrame(ctrl, text="2. Зміна порядку графа (Додати / Видалити місто)")
        lf_nodes.pack(fill=tk.X, pady=4)

        f_n1 = ttk.Frame(lf_nodes)
        f_n1.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(f_n1, text="Назва міста:").pack(side=tk.LEFT)
        self.ent_city_name = ttk.Entry(f_n1, width=15)
        self.ent_city_name.pack(side=tk.LEFT, padx=3)
        self.ent_city_name.insert(0, "Умань")

        f_n2 = ttk.Frame(lf_nodes)
        f_n2.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(f_n2, text="Коорд. X:").pack(side=tk.LEFT)
        self.ent_city_x = ttk.Entry(f_n2, width=6)
        self.ent_city_x.pack(side=tk.LEFT, padx=3)
        self.ent_city_x.insert(0, "400")
        ttk.Label(f_n2, text="Y:").pack(side=tk.LEFT)
        self.ent_city_y = ttk.Entry(f_n2, width=6)
        self.ent_city_y.pack(side=tk.LEFT, padx=3)
        self.ent_city_y.insert(0, "390")

        f_nb = ttk.Frame(lf_nodes)
        f_nb.pack(fill=tk.X, padx=5, pady=3)
        ttk.Button(f_nb, text="+ Додати місто", command=self.add_city).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(f_nb, text="- Видалити місто", command=self.del_city).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        # --- 3. Модифікація розміру графа (Маршрути / Ребра та Дуги) ---
        lf_edges = ttk.LabelFrame(ctrl, text="3. Зміна розміру графа (Додати / Видалити дорогу)")
        lf_edges.pack(fill=tk.X, pady=4)

        f_e1 = ttk.Frame(lf_edges)
        f_e1.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(f_e1, text="Від міста:").pack(side=tk.LEFT)
        self.cb_edge_u = ttk.Combobox(f_e1, width=14)
        self.cb_edge_u.pack(side=tk.LEFT, padx=2)
        ttk.Label(f_e1, text="До:").pack(side=tk.LEFT)
        self.cb_edge_v = ttk.Combobox(f_e1, width=14)
        self.cb_edge_v.pack(side=tk.LEFT, padx=2)

        f_e2 = ttk.Frame(lf_edges)
        f_e2.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(f_e2, text="Віддаль (км):").pack(side=tk.LEFT)
        self.ent_weight = ttk.Entry(f_e2, width=7)
        self.ent_weight.pack(side=tk.LEFT, padx=4)
        self.ent_weight.insert(0, "210")
        ttk.Checkbutton(f_e2, text="Одностороння дуга (U➔V)", variable=self.is_directed).pack(side=tk.LEFT, padx=4)

        f_eb = ttk.Frame(lf_edges)
        f_eb.pack(fill=tk.X, padx=5, pady=3)
        ttk.Button(f_eb, text="+ Додати / Оновити дорогу", command=self.add_road).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(f_eb, text="- Видалити дорогу", command=self.del_road).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        # --- 4. Легенда ---
        lf_leg = ttk.LabelFrame(ctrl, text="Легенда візуалізації")
        lf_leg.pack(fill=tk.X, pady=4)
        for col, txt in [
            ("#E2E8F0", "Не відвідане місто (d = ∞)"),
            ("#FDE047", "У пріоритетній черзі (релаксована вершина)"),
            ("#60A5FA", "Розкрите місто (остаточна мінімальна віддаль)"),
            ("#22C55E", "Місто та траса найкоротшого маршруту")
        ]:
            f = ttk.Frame(lf_leg)
            f.pack(anchor=tk.W, padx=5, pady=1)
            tk.Canvas(f, width=14, height=14, bg=col, highlightthickness=1, highlightbackground="black").pack(side=tk.LEFT)
            ttk.Label(f, text=txt).pack(side=tk.LEFT, padx=5)

        self.lbl_status = ttk.Label(ctrl, text="", font=("Arial", 9, "bold"), justify=tk.LEFT)
        self.lbl_status.pack(pady=4, padx=5, anchor=tk.W)

    def load_ukraine_graph(self):
        # Географічні екранні координати 26 міст України (відповідно до карти рис. 1)
        self.nodes = {
            "Ужгород": (65, 385),
            "Львів": (125, 270),
            "Луцьк": (195, 180),
            "Рівне": (250, 205),
            "Тернопіль": (205, 305),
            "Івано-Франківськ": (155, 365),
            "Чернівці": (215, 435),
            "Хмельницький": (275, 325),
            "Житомир": (350, 235),
            "Вінниця": (355, 345),
            "Київ": (445, 220),
            "Чернігів": (495, 125),
            "Черкаси": (505, 315),
            "Кропивницький": (510, 415),
            "Одеса": (440, 585),
            "Миколаїв": (515, 550),
            "Херсон": (565, 580),
            "Кривий Ріг": (580, 465),
            "Суми": (645, 175),
            "Полтава": (635, 295),
            "Дніпро": (655, 405),
            "Запоріжжя": (675, 475),
            "Мелітополь": (685, 565),
            "Сімферополь": (635, 695),
            "Севастополь": (585, 735),
            "Харків": (725, 260),
            "Донецьк": (805, 445),
            "Маріуполь": (795, 545),
            "Луганськ": (875, 375)
        }

        # Рівно 50 маршрутів згідно з Таблицею 1 методички
        raw_edges = [
            ("Вінниця", "Житомир", 127),
            ("Вінниця", "Київ", 267),
            ("Вінниця", "Кропивницький", 320),
            ("Вінниця", "Миколаїв", 428),
            ("Вінниця", "Одеса", 423),
            ("Вінниця", "Черкаси", 341),
            ("Вінниця", "Чернівці", 276),
            ("Дніпро", "Донецьк", 248),
            ("Дніпро", "Запоріжжя", 85),
            ("Дніпро", "Кропивницький", 244),
            ("Дніпро", "Кривий Ріг", 146),
            ("Дніпро", "Полтава", 160),
            ("Дніпро", "Харків", 218),
            ("Донецьк", "Луганськ", 156),
            ("Донецьк", "Маріуполь", 113),
            ("Донецьк", "Харків", 294),
            ("Запоріжжя", "Мелітополь", 125),
            ("Івано-Франківськ", "Тернопіль", 133),
            ("Івано-Франківськ", "Ужгород", 293),
            ("Київ", "Житомир", 140),
            ("Київ", "Полтава", 340),
            ("Київ", "Суми", 333),
            ("Київ", "Черкаси", 189),
            ("Київ", "Чернігів", 148),
            ("Кропивницький", "Полтава", 246),
            ("Луганськ", "Харків", 325),
            ("Львів", "Івано-Франківськ", 134),
            ("Львів", "Луцьк", 151),
            ("Львів", "Рівне", 211),
            ("Львів", "Тернопіль", 127),
            ("Львів", "Ужгород", 268),
            ("Львів", "Чернівці", 268),
            ("Мелітополь", "Маріуполь", 192),
            ("Мелітополь", "Сімферополь", 250),
            ("Миколаїв", "Херсон", 69),
            ("Рівне", "Житомир", 188),
            ("Рівне", "Луцьк", 73),
            ("Рівне", "Тернопіль", 155),
            ("Харків", "Полтава", 143),
            ("Херсон", "Мелітополь", 231),
            ("Хмельницький", "Вінниця", 119),
            ("Хмельницький", "Житомир", 183),
            ("Хмельницький", "Рівне", 194),
            ("Хмельницький", "Тернопіль", 112),
            ("Хмельницький", "Чернівці", 187),
            ("Суми", "Харків", 184),
            ("Черкаси", "Полтава", 233),
            ("Полтава", "Суми", 175),
            ("Чернігів", "Суми", 306),
            ("Сімферополь", "Севастополь", 81)
        ]

        self.edges = [(u, v, w, False) for u, v, w in raw_edges]
        self.update_comboboxes()
        self.draw_graph()

    def update_comboboxes(self):
        cities = sorted(self.nodes.keys())
        self.cb_start["values"] = cities
        self.cb_goal["values"] = cities
        self.cb_edge_u["values"] = cities
        self.cb_edge_v["values"] = cities
        if self.start_city.get() not in self.nodes and cities:
            self.start_city.set(cities[0])
        if self.goal_city.get() not in self.nodes and cities:
            self.goal_city.set(cities[-1])

    def swap_cities(self):
        s, g = self.start_city.get(), self.goal_city.get()
        self.start_city.set(g)
        self.goal_city.set(s)

    def add_city(self):
        name = self.ent_city_name.get().strip()
        if not name:
            messagebox.showerror("Помилка", "Введіть назву міста!")
            return
        try:
            x, y = int(self.ent_city_x.get()), int(self.ent_city_y.get())
            self.nodes[name] = (x, y)
            self.update_comboboxes()
            self.draw_graph()
        except ValueError:
            messagebox.showerror("Помилка", "Координати X та Y мають бути цілими числами!")

    def del_city(self):
        name = self.ent_city_name.get().strip()
        if name in self.nodes:
            del self.nodes[name]
            self.edges = [(u, v, w, d) for u, v, w, d in self.edges if u != name and v != name]
            self.update_comboboxes()
            self.draw_graph()
        else:
            messagebox.showwarning("Увага", f"Місто «{name}» не знайдено у графі.")

    def add_road(self):
        u = self.cb_edge_u.get().strip()
        v = self.cb_edge_v.get().strip()
        if u not in self.nodes or v not in self.nodes or u == v:
            messagebox.showerror("Помилка", "Оберіть два різні існуючі міста!")
            return
        try:
            w = int(self.ent_weight.get())
            if w <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Помилка", "Віддаль має бути додатним числом (км)!")
            return

        is_dir = self.is_directed.get()
        self.del_road(silent=True)
        self.edges.append((u, v, w, is_dir))
        self.draw_graph()

    def del_road(self, silent=False):
        u = self.cb_edge_u.get().strip()
        v = self.cb_edge_v.get().strip()
        before = len(self.edges)
        self.edges = [
            (a, b, w, d) for a, b, w, d in self.edges
            if not ((a == u and b == v) or (not d and a == v and b == u))
        ]
        if not silent and len(self.edges) == before:
            messagebox.showwarning("Увага", f"Прямого шляху між «{u}» та «{v}» не знайдено.")
        self.draw_graph()

    def draw_graph(self, node_colors=None, path_edges=None, dist_labels=None):
        self.canvas.delete("all")
        node_colors = node_colors or {}
        path_edges = path_edges or set()
        dist_labels = dist_labels or {}

        r = 11
        # 1. Малювання автомобільних шляхів (ребер/дуг) та їх ваг
        for u, v, w, is_dir in self.edges:
            if u not in self.nodes or v not in self.nodes:
                continue
            x1, y1 = self.nodes[u]
            x2, y2 = self.nodes[v]

            is_path = (u, v) in path_edges or (not is_dir and (v, u) in path_edges)
            line_col = "#16A34A" if is_path else ("#DC2626" if is_dir else "#94A3B8")
            line_w = 4.0 if is_path else 1.5

            if is_dir:
                ang = math.atan2(y2 - y1, x2 - x1)
                x2_a = x2 - r * math.cos(ang)
                y2_a = y2 - r * math.sin(ang)
                self.canvas.create_line(x1, y1, x2_a, y2_a, fill=line_col, width=line_w,
                                        arrow=tk.LAST, arrowshape=(9, 11, 4))
            else:
                self.canvas.create_line(x1, y1, x2, y2, fill=line_col, width=line_w)

            # Підпис кілометражу посередині ребра
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            fg_w = "#15803D" if is_path else "#475569"
            font_w = ("Arial", 8, "bold") if is_path else ("Arial", 7)
            self.canvas.create_text(mx, my - 5, text=str(w), font=font_w, fill=fg_w)

        # 2. Малювання міст (вершин) та поточних міток Дейкстри d[v]
        for city, (x, y) in self.nodes.items():
            col = node_colors.get(city, "#E2E8F0")
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=col, outline="#1E293B", width=1.8)
            self.canvas.create_text(x, y - r - 9, text=city, font=("Arial", 9, "bold"), fill="#0F172A")

            if city in dist_labels and dist_labels[city] < float('inf'):
                d_txt = f"{dist_labels[city]} км"
                self.canvas.create_text(x, y + r + 9, text=d_txt, font=("Consolas", 8, "bold"), fill="#B91C1C")

        self.lbl_status.config(
            text=f"Порядок графа (міст): {len(self.nodes)} | Розмір графа (доріг): {len(self.edges)}\n"
                 f"Маршрут: {self.start_city.get()} ➔ {self.goal_city.get()}"
        )
        self.root.update()

    def get_neighbors(self, u):
        res = []
        for a, b, w, is_dir in self.edges:
            if a == u and b in self.nodes:
                res.append((b, w))
            elif not is_dir and b == u and a in self.nodes:
                res.append((a, w))
        return res

    def execute_dijkstra(self, start, goal, animate=True):
        dist = {city: float('inf') for city in self.nodes}
        parent = {city: None for city in self.nodes}
        dist[start] = 0

        # Пріоритетна черга зберігає кортежі (поточна_віддаль_км, назва_міста)
        pq = [(0, start)]
        visited = set()
        expanded_order = []
        node_colors = {start: "#FDE047"}
        cycles = 0
        relaxations = 0
        found = False

        t0 = time.perf_counter()

        while pq:
            curr_d, u = heapq.heappop(pq)
            if u in visited:
                continue

            cycles += 1
            visited.add(u)
            expanded_order.append((u, curr_d))
            node_colors[u] = "#60A5FA"

            if u == goal:
                found = True
                break

            for v, weight in self.get_neighbors(u):
                if v not in visited:
                    new_d = curr_d + weight
                    if new_d < dist[v]:
                        dist[v] = new_d
                        parent[v] = u
                        relaxations += 1
                        heapq.heappush(pq, (new_d, v))
                        node_colors[v] = "#FDE047"

            if animate and self.anim_speed.get() > 0:
                self.draw_graph(node_colors, dist_labels=dist)
                time.sleep(self.anim_speed.get())

        dt_ms = max(0.001, (time.perf_counter() - t0) * 1000.0 -
                    (cycles * self.anim_speed.get() * 1000.0 if animate else 0))

        path = []
        if found:
            curr = goal
            while curr is not None:
                path.append(curr)
                curr = parent[curr]
            path.reverse()

        return found, path, dist[goal], cycles, relaxations, expanded_order, dt_ms, node_colors, dist

    def run_dijkstra(self):
        start = self.start_city.get()
        goal = self.goal_city.get()
        if start not in self.nodes or goal not in self.nodes:
            messagebox.showerror("Помилка", "Оберіть коректні міста зі списку!")
            return

        found, path, total_km, cycles, relax, expanded, dt_ms, colors, dist = self.execute_dijkstra(start, goal, True)

        path_edges = set()
        if found:
            for i in range(len(path) - 1):
                path_edges.add((path[i], path[i + 1]))
            for c in path:
                colors[c] = "#22C55E"

        self.draw_graph(colors, path_edges, dist)
        self.show_report_window(start, goal, found, path, total_km, cycles, relax, expanded, dt_ms)

    def show_report_window(self, start, goal, found, path, total_km, cycles, relax, expanded, dt_ms):
        win = tk.Toplevel(self.root)
        win.title("Результати пошуку найкоротшого шляху (Алгоритм Дейкстри)")
        win.geometry("640x480")

        txt = tk.Text(win, font=("Consolas", 10), wrap=tk.WORD, padx=10, pady=10)
        txt.pack(fill=tk.BOTH, expand=True)

        out = "=== ЗВІТ: ПОШУК НАЙКОРОТШОГО ШЛЯХУ ЗА АЛГОРИТМОМ ДЕЙКСТРИ ===\n\n"
        out += f"Порядок графа (кількість міст): {len(self.nodes)}\n"
        out += f"Розмір графа (кількість автошляхів): {len(self.edges)}\n"
        out += f"Заданий напрямок: {start} ➔ {goal}\n"
        out += "-" * 60 + "\n"

        if found:
            out += f"СТАТУС: Найкоротший маршрут УСПІШНО знайдено!\n"
            out += f"ЗАГАЛЬНА ВІДДАЛЬ МАРШРУТУ: {total_km} км\n"
            out += f"Кількість транзитних ділянок (ребер): {len(path)-1} (міст у шляху: {len(path)})\n\n"
            out += "Детальний маршрут по ділянках:\n"
            acc = 0
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                w = next(wt for a, b, wt, d in self.edges if (a == u and b == v) or (not d and a == v and b == u))
                acc += w
                out += f"  {i+1}. {u} ➔ {v} : +{w} км (накопичено: {acc} км)\n"
            out += f"\nПерелік міст найкоротшого шляху:\n  " + " ➔ ".join(path) + "\n\n"
        else:
            out += "СТАТУС: Маршрут НЕ ЗНАЙДЕНО (цільове місто недосяжне).\n\n"

        out += f"Кількість циклів розкриття вершин: {cycles}\n"
        out += f"Кількість успішних релаксацій (оновлень міток відстані): {relax}\n"
        out += f"Кількість розкритих міст: {len(expanded)} із {len(self.nodes)}\n"
        out += "Порядок зафіксованих міст (місто: мінімальна віддаль км):\n  "
        out += ", ".join(f"{c} ({d} км)" for c, d in expanded) + "\n\n"
        out += f"Чистий час обчислення: {dt_ms:.4f} мс\n"

        txt.insert(tk.END, out)
        txt.config(state=tk.DISABLED)

    def compare_dijkstra_vs_bfs(self):
        # Порівняння зваженого пошуку Дейкстри проти незваженого пошуку в ширину (BFS)
        start, goal = self.start_city.get(), self.goal_city.get()
        f_d, path_d, km_d, cyc_d, _, _, dt_d, _, _ = self.execute_dijkstra(start, goal, animate=False)

        # Класичний BFS (ігнорує кілометраж, мінімізує лише кількість проміжних міст)
        from collections import deque
        q = deque([(start, [start])])
        vis = {start}
        path_bfs = []
        cyc_bfs = 0
        while q:
            cyc_bfs += 1
            curr, p = q.popleft()
            if curr == goal:
                path_bfs = p
                break
            for nxt, _ in sorted(self.get_neighbors(curr)):
                if nxt not in vis:
                    vis.add(nxt)
                    q.append((nxt, p + [nxt]))

        km_bfs = 0
        if path_bfs:
            for i in range(len(path_bfs) - 1):
                u, v = path_bfs[i], path_bfs[i + 1]
                km_bfs += next(wt for a, b, wt, d in self.edges if (a == u and b == v) or (not d and a == v and b == u))

        win = tk.Toplevel(self.root)
        win.title("Порівняння: Алгоритм Дейкстри проти сліпого Пошуку в ширину (BFS)")
        win.geometry("680x400")
        txt = tk.Text(win, font=("Consolas", 10), wrap=tk.WORD, padx=10, pady=10)
        txt.pack(fill=tk.BOTH, expand=True)

        out = f"=== ПОРІВНЯННЯ: АЛГОРИТМ ДЕЙКСТРИ vs ПОШУК В ШИРИНУ (BFS) ===\n"
        out += f"Маршрут: {start} ➔ {goal}\n" + "=" * 62 + "\n\n"
        if f_d and path_bfs:
            out += f"1. СЛІПИЙ ПОШУК В ШИРИНУ (BFS — мінімізує лише к-сть ребер):\n"
            out += f"   • Шлях ({len(path_bfs)-1} ділянок): {' ➔ '.join(path_bfs)}\n"
            out += f"   • Реальна віддаль по кілометражу: {km_bfs} км\n\n"
            out += f"2. АЛГОРИТМ ДЕЙКСТРИ (враховує ваги ребер у км):\n"
            out += f"   • Шлях ({len(path_d)-1} ділянок): {' ➔ '.join(path_d)}\n"
            out += f"   • Мінімальна віддаль: {km_d} км\n\n"
            out += f"★ ВИСНОВОК: Алгоритм Дейкстри заощадив {km_bfs - km_d} км шляху!\n"
        else:
            out += "Шлях не знайдено.\n"

        txt.insert(tk.END, out)
        txt.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = DijkstraUkraineApp(root)
    root.mainloop()