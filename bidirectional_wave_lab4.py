import tkinter as tk
from tkinter import ttk, messagebox
import time

class BidirectionalWaveLab4App:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторна робота №4: Двонаправлений хвильовий пошук на одиничному графі")
        self.root.geometry("1280x820")

        self.grid_size = tk.IntVar(value=15)
        # 0 - Ортогональний (4 напр.), 1 - Діагональний (4 напр.), 2 - Комбінований (8 напр.)
        self.operator_type = tk.IntVar(value=0)
        # 0 - Малювати стіни (0/-1), 1 - Старт S, 2 - Мета G
        self.edit_mode = tk.IntVar(value=0)
        self.anim_speed = tk.DoubleVar(value=0.10)

        self.grid_data = []
        self.wave_start = []  # Матриця прямої хвилі (від S)
        self.wave_goal = []   # Матриця зустрічної хвилі (від G)
        self.start_pos = (1, 1)
        self.goal_pos = (13, 13)
        self.meet_node = None
        self.last_ordered_path = []

        self.setup_ui()
        self.load_preset_maze(15)

    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Полотно візуалізації матриці-лабіринту
        self.canvas = tk.Canvas(main_frame, bg="white", width=830, height=790, relief=tk.SUNKEN, bd=2)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)

        # Панель керування
        ctrl = ttk.Frame(main_frame, width=420)
        ctrl.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        # --- 1. Розмірність і порядок графа ---
        lf_size = ttk.LabelFrame(ctrl, text="1. Розмірність і вигляд матриці-лабіринту")
        lf_size.pack(fill=tk.X, pady=3)

        f_sz = ttk.Frame(lf_size)
        f_sz.pack(fill=tk.X, padx=5, pady=3)
        ttk.Label(f_sz, text="Порядок матриці (N x N, 10..20):").pack(side=tk.LEFT)
        spin_n = ttk.Spinbox(f_sz, from_=10, to=20, textvariable=self.grid_size, width=5)
        spin_n.pack(side=tk.LEFT, padx=5)
        ttk.Button(f_sz, text="Застосувати N", command=lambda: self.load_preset_maze(self.grid_size.get())).pack(side=tk.LEFT)

        f_pres = ttk.Frame(lf_size)
        f_pres.pack(fill=tk.X, padx=5, pady=3)
        ttk.Button(f_pres, text="Базовий лабіринт", command=lambda: self.load_preset_maze(self.grid_size.get())).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(f_pres, text="Очистити стіни (усі 0)", command=self.clear_walls).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(f_pres, text="+ Щільність стін", command=self.add_more_obstacles).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        # --- 2. Редагування лабіринту ---
        lf_edit = ttk.LabelFrame(ctrl, text="2. Редагування матриці та вершин (клік миші)")
        lf_edit.pack(fill=tk.X, pady=3)
        for val, txt in [
            (0, "Змінювати клітинку: Прохідна (0) ⇄ Непрохідна (-1)"),
            (1, "Встановити ПОЧАТКОВУ вершину (Старт S)"),
            (2, "Встановити ЦІЛЬОВУ вершину (Мета G)")
        ]:
            ttk.Radiobutton(lf_edit, text=txt, variable=self.edit_mode, value=val).pack(anchor=tk.W, padx=8, pady=1)

        ttk.Button(lf_edit, text="⇄ Поміняти місцями Старт і Мету (Реверс)", command=self.swap_start_goal).pack(fill=tk.X, padx=5, pady=3)

        # --- 3. Оператор переходу ---
        lf_op = ttk.LabelFrame(ctrl, text="3. Оператор переходу")
        lf_op.pack(fill=tk.X, pady=3)
        for val, txt in [
            (0, "Оператор 1: «Вверх-вниз-вправо-вліво» (4 ортогональні)"),
            (1, "Оператор 2: «Перехід по діагоналях» (4 діагональні)"),
            (2, "Оператор 3: Комбінований (8 напрямків)")
        ]:
            ttk.Radiobutton(lf_op, text=txt, variable=self.operator_type, value=val).pack(anchor=tk.W, padx=8, pady=1)

        # --- 4. Керування запуском та порівнянням ---
        lf_run = ttk.LabelFrame(ctrl, text="4. Запуск двонаправленого пошуку та дослідження")
        lf_run.pack(fill=tk.X, pady=3)

        ttk.Label(lf_run, text="Час затримки покрокової анімації (сек):").pack(anchor=tk.W, padx=5, pady=1)
        ttk.Scale(lf_run, from_=0.0, to=0.4, variable=self.anim_speed, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5)

        ttk.Button(lf_run, text="▶ ЗАПУСТИТИ ДВОНАПРАВЛЕНИЙ ХВИЛЬОВИЙ ПОШУК", command=self.run_bidirectional_search).pack(fill=tk.X, padx=5, pady=4)
        ttk.Button(lf_run, text="⚔ ПОРІВНЯТИ 3 ОПЕРАТОРИ (Двонаправлений)", command=self.compare_all_operators).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(lf_run, text="⚡ ДВОНАПРАВЛЕНИЙ vs ОДНОНАПРАВЛЕНИЙ (Порівняння)", command=self.compare_bi_vs_uni).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(lf_run, text="Скинути хвилі (показати вихідну матрицю 0 та -1)", command=self.reset_waves).pack(fill=tk.X, padx=5, pady=3)

        # --- 5. Легенда ---
        lf_leg = ttk.LabelFrame(ctrl, text="Легенда")
        lf_leg.pack(fill=tk.X, pady=3)
        for col, txt in [
            ("#FFFFFF", "0 : Прохідна вершина лабіринту"),
            ("#37474F", "-1 : Непрохідна вершина (стіна)"),
            ("#B3E5FC", "Пряма хвиля (від Старту S, мітки +d)"),
            ("#F8BBD0", "Зустрічна хвиля (від Мети G, мітки -d)"),
            ("#FFF176", "Активні фронти обох хвиль на поточному кроці"),
            ("#AB47BC", "Вершина зустрічі двох хвиль (точка стиковки)"),
            ("#66BB6A", "Знайдений найкоротший шлях")
        ]:
            f = ttk.Frame(lf_leg)
            f.pack(anchor=tk.W, padx=5, pady=1)
            tk.Canvas(f, width=14, height=14, bg=col, highlightthickness=1, highlightbackground="black").pack(side=tk.LEFT)
            ttk.Label(f, text=txt).pack(side=tk.LEFT, padx=5)

        self.lbl_stats = ttk.Label(ctrl, text="", font=("Arial", 9, "bold"), justify=tk.LEFT)
        self.lbl_stats.pack(pady=4, padx=5, anchor=tk.W)

    def load_preset_maze(self, n):
        n = max(10, min(20, int(n)))
        self.grid_size.set(n)
        self.grid_data = [[0 for _ in range(n)] for _ in range(n)]
        self.start_pos = (1, 1)
        self.goal_pos = (n - 2, n - 2)

        for i in range(n):
            if 2 <= i <= n - 4:
                self.grid_data[i][n // 3] = -1
            if 3 <= i <= n - 2:
                self.grid_data[i][(2 * n) // 3] = -1
            if 2 <= i <= n // 2:
                self.grid_data[n // 2][i] = -1

        self.grid_data[n // 3][n // 3] = 0
        self.grid_data[(2 * n) // 3][(2 * n) // 3] = 0
        self.grid_data[self.start_pos[0]][self.start_pos[1]] = 0
        self.grid_data[self.goal_pos[0]][self.goal_pos[1]] = 0

        self.reset_waves()

    def clear_walls(self):
        n = self.grid_size.get()
        self.grid_data = [[0 for _ in range(n)] for _ in range(n)]
        self.reset_waves()

    def add_more_obstacles(self):
        n = self.grid_size.get()
        for r in range(1, n - 1, 2):
            for c in range(2, n - 1, 3):
                if (r, c) != self.start_pos and (r, c) != self.goal_pos:
                    self.grid_data[r][c] = -1
        self.reset_waves()

    def swap_start_goal(self):
        self.start_pos, self.goal_pos = self.goal_pos, self.start_pos
        self.reset_waves()

    def reset_waves(self):
        n = self.grid_size.get()
        self.wave_start = [[None for _ in range(n)] for _ in range(n)]
        self.wave_goal = [[None for _ in range(n)] for _ in range(n)]
        self.meet_node = None
        self.last_ordered_path = []
        self.draw_maze()

    def on_canvas_click(self, event):
        n = self.grid_size.get()
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        cell_sz = min(w, h) // (n + 1)
        ox, oy = (w - cell_sz * n) // 2, (h - cell_sz * n) // 2
        c, r = (event.x - ox) // cell_sz, (event.y - oy) // cell_sz

        if 0 <= r < n and 0 <= c < n:
            mode = self.edit_mode.get()
            if mode == 0 and (r, c) not in (self.start_pos, self.goal_pos):
                self.grid_data[r][c] = 0 if self.grid_data[r][c] == -1 else -1
            elif mode == 1 and (r, c) != self.goal_pos and self.grid_data[r][c] == 0:
                self.start_pos = (r, c)
            elif mode == 2 and (r, c) != self.start_pos and self.grid_data[r][c] == 0:
                self.goal_pos = (r, c)
            self.reset_waves()

    def on_canvas_drag(self, event):
        if self.edit_mode.get() == 0:
            n = self.grid_size.get()
            w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
            cell_sz = min(w, h) // (n + 1)
            ox, oy = (w - cell_sz * n) // 2, (h - cell_sz * n) // 2
            c, r = (event.x - ox) // cell_sz, (event.y - oy) // cell_sz
            if 0 <= r < n and 0 <= c < n and (r, c) not in (self.start_pos, self.goal_pos):
                self.grid_data[r][c] = -1
                self.reset_waves()

    def draw_maze(self, front_s=None, front_g=None, path_set=None):
        self.canvas.delete("all")
        front_s = front_s or set()
        front_g = front_g or set()
        path_set = path_set or set()

        n = self.grid_size.get()
        w = max(800, self.canvas.winfo_width())
        h = max(760, self.canvas.winfo_height())
        cell_sz = min(w, h) // (n + 1)
        ox = (w - cell_sz * n) // 2
        oy = (h - cell_sz * n) // 2

        passable_cnt = 0
        wall_cnt = 0

        for r in range(n):
            for c in range(n):
                x1, y1 = ox + c * cell_sz, oy + r * cell_sz
                x2, y2 = x1 + cell_sz, y1 + cell_sz

                val = self.grid_data[r][c]
                ws = self.wave_start[r][c]
                wg = self.wave_goal[r][c]

                if val == -1:
                    wall_cnt += 1
                    bg_col, fg_col, txt = "#37474F", "#ECEFF1", "-1"
                else:
                    passable_cnt += 1
                    bg_col, fg_col, txt = "#FFFFFF", "#212121", "0"

                    if ws is not None and wg is not None:
                        bg_col = "#CE93D8"
                        txt = f"+{ws}/-{wg}"
                    elif ws is not None:
                        bg_col = "#B3E5FC"
                        txt = f"+{ws}"
                    elif wg is not None:
                        bg_col = "#F8BBD0"
                        txt = f"-{wg}"

                    if (r, c) in front_s or (r, c) in front_g:
                        bg_col = "#FFF176"
                    if (r, c) in path_set:
                        bg_col, fg_col = "#66BB6A", "#FFFFFF"
                    if (r, c) == self.meet_node:
                        bg_col, fg_col = "#AB47BC", "#FFFFFF"
                    if (r, c) == self.start_pos:
                        bg_col, fg_col = "#FF8A65", "#000000"
                        txt = "S(0)"
                    elif (r, c) == self.goal_pos:
                        bg_col, fg_col = "#FF7043", "#000000"
                        txt = "G(0)"

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=bg_col, outline="#90A4AE", width=1)
                self.canvas.create_text(x1 + 14, y1 + 8, text=f"{r},{c}", font=("Arial", 7), fill="#78909C")
                self.canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2 + 3, text=txt,
                                        font=("Consolas", 9, "bold"), fill=fg_col)

        if len(self.last_ordered_path) > 1:
            pts = []
            for r, c in self.last_ordered_path:
                pts.extend([ox + c * cell_sz + cell_sz // 2, oy + r * cell_sz + cell_sz // 2])
            if len(pts) >= 4:
                self.canvas.create_line(*pts, fill="#1B5E20", width=3, arrow=tk.LAST)

        total = n * n
        self.lbl_stats.config(
            text=f"Матриця: {n}x{n} (Всього {total} вершин)\n"
                 f"Прохідних (0): {passable_cnt} ({passable_cnt/total*100:.1f}%) | Непрохідних (-1): {wall_cnt} ({wall_cnt/total*100:.1f}%)\n"
                 f"Старт S: {self.start_pos} | Мета G: {self.goal_pos}"
        )
        self.root.update()

    def get_deltas(self, op_type):
        if op_type == 0:
            return [(-1, 0), (1, 0), (0, 1), (0, -1)]
        elif op_type == 1:
            return [(-1, -1), (-1, 1), (1, 1), (1, -1)]
        else:
            return [(-1, 0), (1, 0), (0, 1), (0, -1), (-1, -1), (-1, 1), (1, 1), (1, -1)]

    def execute_bidirectional_wave(self, op_type, animate=True):
        n = self.grid_size.get()
        ws = [[None for _ in range(n)] for _ in range(n)]
        wg = [[None for _ in range(n)] for _ in range(n)]
        deltas = self.get_deltas(op_type)

        sr, sc = self.start_pos
        gr, gc = self.goal_pos

        ws[sr][sc] = 0
        wg[gr][gc] = 0

        front_s = [(sr, sc)]
        front_g = [(gr, gc)]
        expanded_nodes = {(sr, sc), (gr, gc)}
        cycles = 0
        meet_cell = (sr, sc) if (sr, sc) == (gr, gc) else None

        t0 = time.perf_counter()

        # ЕТАП 1: Зустрічне поширення двох хвиль (від S та від G)
        while front_s and front_g and meet_cell is None:
            cycles += 1

            # Крок прямої хвилі (від S)
            next_s = []
            for r, c in front_s:
                d = ws[r][c]
                for dr, dc in deltas:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n and self.grid_data[nr][nc] == 0:
                        if ws[nr][nc] is None:
                            ws[nr][nc] = d + 1
                            next_s.append((nr, nc))
                            expanded_nodes.add((nr, nc))
                            if wg[nr][nc] is not None and meet_cell is None:
                                meet_cell = (nr, nc)
            front_s = next_s

            if meet_cell is not None:
                if animate and self.anim_speed.get() > 0:
                    self.wave_start, self.wave_goal = ws, wg
                    self.draw_maze(set(front_s), set(front_g))
                    time.sleep(self.anim_speed.get())
                break

            # Крок зустрічної хвилі (від G)
            next_g = []
            for r, c in front_g:
                d = wg[r][c]
                for dr, dc in deltas:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n and self.grid_data[nr][nc] == 0:
                        if wg[nr][nc] is None:
                            wg[nr][nc] = d + 1
                            next_g.append((nr, nc))
                            expanded_nodes.add((nr, nc))
                            if ws[nr][nc] is not None and meet_cell is None:
                                meet_cell = (nr, nc)
            front_g = next_g

            if animate and self.anim_speed.get() > 0:
                self.wave_start, self.wave_goal = ws, wg
                self.draw_maze(set(front_s), set(front_g))
                time.sleep(self.anim_speed.get())

        # ЕТАП 2: Двостороннє відновлення найкоротшого шляху від точки зустрічі M
        path = []
        if meet_cell is not None:
            # 2.1. Від точки зустрічі M назад до S
            path_to_s = [meet_cell]
            curr = meet_cell
            while curr != (sr, sc):
                cr, cc = curr
                cd = ws[cr][cc]
                for dr, dc in deltas:
                    pr, pc = cr + dr, cc + dc
                    if 0 <= pr < n and 0 <= pc < n and ws[pr][pc] == cd - 1:
                        curr = (pr, pc)
                        path_to_s.append(curr)
                        break
            path_to_s.reverse()

            # 2.2. Від точки зустрічі M вперед до G
            path_to_g = []
            curr = meet_cell
            while curr != (gr, gc):
                cr, cc = curr
                cd = wg[cr][cc]
                for dr, dc in deltas:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < n and 0 <= nc < n and wg[nr][nc] == cd - 1:
                        curr = (nr, nc)
                        path_to_g.append(curr)
                        break

            path = path_to_s + path_to_g

        dt_ms = max(0.001, (time.perf_counter() - t0) * 1000.0 -
                    (cycles * self.anim_speed.get() * 1000.0 if animate else 0))

        return (meet_cell is not None), path, meet_cell, cycles, len(expanded_nodes), dt_ms, ws, wg

    def execute_unidirectional_wave(self, op_type):
        # Однонаправлений хвильовий пошук для точного порівняння в одних умовах
        n = self.grid_size.get()
        w = [[None for _ in range(n)] for _ in range(n)]
        deltas = self.get_deltas(op_type)
        sr, sc = self.start_pos
        gr, gc = self.goal_pos
        w[sr][sc] = 0
        front = [(sr, sc)]
        expanded = 1
        cycles = 0
        found = (sr == gr and sc == gc)

        t0 = time.perf_counter()
        while front and not found:
            cycles += 1
            nxt_front = []
            for r, c in front:
                d = w[r][c]
                for dr, dc in deltas:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n and self.grid_data[nr][nc] == 0 and w[nr][nc] is None:
                        w[nr][nc] = d + 1
                        nxt_front.append((nr, nc))
                        expanded += 1
                        if (nr, nc) == (gr, gc):
                            found = True
            front = nxt_front

        dt_ms = max(0.001, (time.perf_counter() - t0) * 1000.0)
        dist = w[gr][gc] if found else None
        return found, dist, cycles, expanded, dt_ms

    def run_bidirectional_search(self):
        op = self.operator_type.get()
        found, path, meet, cycles, exp_cnt, dt_ms, ws, wg = self.execute_bidirectional_wave(op, animate=True)
        self.wave_start, self.wave_goal = ws, wg
        self.meet_node = meet
        self.last_ordered_path = path
        self.draw_maze(path_set=set(path))
        self.show_single_report(op, found, path, meet, cycles, exp_cnt, dt_ms)

    def show_single_report(self, op, found, path, meet, cycles, exp_cnt, dt_ms):
        win = tk.Toplevel(self.root)
        win.title("Результати двонаправленого хвильового пошуку")
        win.geometry("600x460")

        txt = tk.Text(win, font=("Consolas", 10), wrap=tk.WORD, padx=10, pady=10)
        txt.pack(fill=tk.BOTH, expand=True)

        op_names = [
            "«Вверх-вниз-вправо-вліво» (4 ортогональні напрямки)",
            "«Перехід по діагоналях» (4 діагональні напрямки)",
            "Комбінований оператор (8 напрямків)"
        ]
        n = self.grid_size.get()
        passable = sum(1 for r in range(n) for c in range(n) if self.grid_data[r][c] == 0)

        out = "=== ЗВІТ: ДВОНАПРАВЛЕНИЙ ХВИЛЬОВИЙ ПОШУК ===\n\n"
        out += f"Розмірність матриці лабіринту: {n}x{n} ({n*n} вершин)\n"
        out += f"Прохідних (0): {passable} | Непрохідних (-1): {n*n - passable}\n"
        out += f"Оператор переходу: {op_names[op]}\n"
        out += f"Маршрут: Старт S{self.start_pos} ➔ Мета G{self.goal_pos}\n"
        out += "-" * 56 + "\n"

        if found:
            out += f"СТАТУС: Найкоротший шлях УСПІШНО знайдено!\n"
            out += f"Точка зустрічі двох хвиль: M{meet}\n"
            out += f"Віддаль (кількість кроків переходу): {len(path)-1}\n"
            out += f"Кількість вершин у найкоротшому шляху: {len(path)}\n"
            out += f"Координати вершин найкоротшого шляху:\n  " + " ➔ ".join(str(p) for p in path) + "\n\n"
        else:
            out += "СТАТУС: Шлях НЕ ЗНАЙДЕНО (хвилі не змогли зустрітися).\n\n"

        out += f"Кількість циклів роботи (зустрічних кроків): {cycles}\n"
        out += f"Сумарна кількість розкритих вершин обома хвилями: {exp_cnt} (із {passable})\n"
        out += f"Чистий час здійснення пошуку: {dt_ms:.4f} мс\n"

        txt.insert(tk.END, out)
        txt.config(state=tk.DISABLED)

    def compare_all_operators(self):
        win = tk.Toplevel(self.root)
        win.title("Порівняння операторів переходу при двонаправленому пошуку")
        win.geometry("720x520")

        txt = tk.Text(win, font=("Consolas", 10), wrap=tk.WORD, padx=10, pady=10)
        txt.pack(fill=tk.BOTH, expand=True)

        n = self.grid_size.get()
        passable = sum(1 for r in range(n) for c in range(n) if self.grid_data[r][c] == 0)

        out = "=== ПОРІВНЯННЯ ОПЕРАТОРІВ (ДВОНАПРАВЛЕНИЙ ХВИЛЬОВИЙ ПОШУК) ===\n"
        out += f"Матриця: {n}x{n} | Прохідних (0): {passable} | Маршрут: S{self.start_pos} ➔ G{self.goal_pos}\n"
        out += "=" * 66 + "\n\n"

        op_names = [
            "1. Оператор «Вверх-вниз-вправо-вліво» (4 ортогональні)",
            "2. Оператор «Перехід по діагоналях» (4 діагональні)",
            "3. Комбінований оператор (8 напрямків)"
        ]

        for op_idx in range(3):
            found, path, meet, cycles, exp_cnt, dt_ms, _, _ = self.execute_bidirectional_wave(op_idx, animate=False)
            out += f"▶ {op_names[op_idx]}:\n"
            if found:
                out += f"  • Знайдено! Точка зустрічі хвиль: M{meet}\n"
                out += f"  • Віддаль: {len(path)-1} кроків ({len(path)} вершин у шляху)\n"
                out += f"  • Шлях: {' ➔ '.join(str(p) for p in path)}\n"
            else:
                out += f"  • ШЛЯХ НЕ ЗНАЙДЕНО\n"
            out += f"  • Кількість циклів (ітерацій): {cycles}\n"
            out += f"  • Розкрито вершин (сумарно): {exp_cnt}\n"
            out += f"  • Час пошуку: {dt_ms:.4f} мс\n"
            out += "-" * 66 + "\n"

        txt.insert(tk.END, out)
        txt.config(state=tk.DISABLED)

    def compare_bi_vs_uni(self):
        win = tk.Toplevel(self.root)
        win.title("Порівняння: Двонаправлений проти Однонаправленого хвильового пошуку")
        win.geometry("760x540")

        txt = tk.Text(win, font=("Consolas", 10), wrap=tk.WORD, padx=10, pady=10)
        txt.pack(fill=tk.BOTH, expand=True)

        n = self.grid_size.get()
        passable = sum(1 for r in range(n) for c in range(n) if self.grid_data[r][c] == 0)

        out = "=== ЕФЕКТИВНІСТЬ: ДВОНАПРАВЛЕНИЙ vs ОДНОНАПРАВЛЕНИЙ ПОШУК ===\n"
        out += f"Матриця: {n}x{n} | Прохідних (0): {passable} | Маршрут: S{self.start_pos} ➔ G{self.goal_pos}\n"
        out += "=" * 70 + "\n\n"

        op_names = [
            "1. Оператор «Вверх-вниз-вправо-вліво» (4 ортогональні)",
            "2. Оператор «Перехід по діагоналях» (4 діагональні)",
            "3. Комбінований оператор (8 напрямків)"
        ]

        for op_idx in range(3):
            f_bi, path_bi, meet_bi, cyc_bi, exp_bi, dt_bi, _, _ = self.execute_bidirectional_wave(op_idx, animate=False)
            f_uni, dist_uni, cyc_uni, exp_uni, dt_uni = self.execute_unidirectional_wave(op_idx)

            out += f"▶ {op_names[op_idx]}:\n"
            if f_bi and f_uni:
                saved_cyc = ((cyc_uni - cyc_bi) / cyc_uni) * 100 if cyc_uni else 0
                saved_exp = ((exp_uni - exp_bi) / exp_uni) * 100 if exp_uni else 0
                out += f"  • Довжина шляху (однакова): {len(path_bi)-1} кроків ({len(path_bi)} вершин)\n"
                out += f"  • ОДНОНАПРАВЛЕНИЙ: Циклів = {cyc_uni:2d} | Розкрито вершин = {exp_uni:3d} | Час = {dt_uni:.4f} мс\n"
                out += f"  • ДВОНАПРАВЛЕНИЙ : Циклів = {cyc_bi:2d} | Розкрито вершин = {exp_bi:3d} | Час = {dt_bi:.4f} мс (Зустріч у {meet_bi})\n"
                out += f"  ★ ВИГРАШ ДВОНАПРАВЛЕНОГО: Скорочення циклів на {saved_cyc:.1f}%, розкритих вершин на {saved_exp:.1f}%!\n"
            else:
                out += f"  • Шлях не знайдено (Циклів Однонапр.: {cyc_uni}, Двонапр.: {cyc_bi})\n"
            out += "-" * 70 + "\n"

        txt.insert(tk.END, out)
        txt.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = BidirectionalWaveLab4App(root)
    root.mainloop()