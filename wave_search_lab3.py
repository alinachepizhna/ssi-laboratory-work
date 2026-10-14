import tkinter as tk
from tkinter import ttk, messagebox
import time

class WaveSearchLab3App:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторна робота №3: Одно-направлений хвильовий пошук (Алгоритм Лі)")
        self.root.geometry("1260x800")

        self.grid_size = tk.IntVar(value=15)  # Розмірність матриці N x N (від 10 до 20)
        # Оператор переходу: 0 - Ортогональний (4 напр.), 1 - Діагональний (4 напр.), 2 - Комбінований (8 напр.)
        self.operator_type = tk.IntVar(value=0)
        # Режим кліку миші: 0 - Стіна (-1)/Прохід (0), 1 - Встановити Старт, 2 - Встановити Мету
        self.edit_mode = tk.IntVar(value=0)
        self.anim_speed = tk.DoubleVar(value=0.08)

        self.grid_data = []    # Матриця лабіринту: 0 (прохідна), -1 (стіна)
        self.wave_matrix = []  # Матриця значень фронту хвилі
        self.start_pos = (1, 1)
        self.goal_pos = (13, 13)

        self.setup_ui()
        self.load_preset_maze(15)

    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Полотно для відображення матриці лабіринту
        self.canvas = tk.Canvas(main_frame, bg="white", width=820, height=780, relief=tk.SUNKEN, bd=2)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)

        # Панель керування
        ctrl = ttk.Frame(main_frame, width=410)
        ctrl.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        # --- 1. Розмірність і пресети ---
        lf_size = ttk.LabelFrame(ctrl, text="1. Розмірність та структура лабіринту")
        lf_size.pack(fill=tk.X, pady=4)

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

        # --- 2. Редагування лабіринту мишкою ---
        lf_edit = ttk.LabelFrame(ctrl, text="2. Інтерактивне редагування (клік по клітинці)")
        lf_edit.pack(fill=tk.X, pady=4)
        for val, txt in [
            (0, "Малювати / Стирати перешкоди (0 ⇄ -1)"),
            (1, "Встановити ПОЧАТКОВУ вершину (Старт S)"),
            (2, "Встановити ЦІЛЬОВУ вершину (Мета G)")
        ]:
            ttk.Radiobutton(lf_edit, text=txt, variable=self.edit_mode, value=val).pack(anchor=tk.W, padx=8, pady=1)

        ttk.Button(lf_edit, text="⇄ Поміняти місцями Старт і Мету (Реверс)", command=self.swap_start_goal).pack(fill=tk.X, padx=5, pady=3)

        # --- 3. Оператор переходу ---
        lf_op = ttk.LabelFrame(ctrl, text="3. Оператор переходу (поширення хвилі)")
        lf_op.pack(fill=tk.X, pady=4)
        for val, txt in [
            (0, "Оператор 1: «Вверх-вниз-вправо-вліво» (4 напр., Манхеттен)"),
            (1, "Оператор 2: «Перехід по діагоналях» (4 напр., тільки навскіс)"),
            (2, "Оператор 3: Комбінований (8 напрямків, окіл Мура)")
        ]:
            ttk.Radiobutton(lf_op, text=txt, variable=self.operator_type, value=val).pack(anchor=tk.W, padx=8, pady=2)

        # --- 4. Керування запуском ---
        lf_run = ttk.LabelFrame(ctrl, text="4. Керування пошуком та візуалізацією")
        lf_run.pack(fill=tk.X, pady=4)

        ttk.Label(lf_run, text="Час затримки поширення фронту хвилі (сек):").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Scale(lf_run, from_=0.0, to=0.4, variable=self.anim_speed, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5)

        ttk.Button(lf_run, text="▶ ЗАПУСТИТИ ОДНО-НАПРАВЛЕНИЙ ХВИЛЬОВИЙ ПОШУК", command=self.run_wave_search).pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(lf_run, text="⚔ ПОРІВНЯТИ ВСІ 3 ОПЕРАТОРИ ПЕРЕХОДУ", command=self.compare_operators).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(lf_run, text="Скинути хвилю (показати вихідні 0 та -1)", command=self.reset_wave_view).pack(fill=tk.X, padx=5, pady=3)

        # --- 5. Легенда ---
        lf_leg = ttk.LabelFrame(ctrl, text="Легенда")
        lf_leg.pack(fill=tk.X, pady=4)
        for col, txt in [
            ("#FFFFFF", "0 : Прохідна ділянка лабіринту"),
            ("#37474F", "-1 : Непрохідна ділянка (стіна)"),
            ("#FFF176", "Поточний фронт хвилі (активний рівень d)"),
            ("#B3E5FC", "Розкриті вершини (пройдена хвиля 1..d-1)"),
            ("#66BB6A", "Відновлений найкоротший шлях (зворотний хід)"),
            ("#FF8A65", "S / G : Початкова та Цільова вершини")
        ]:
            f = ttk.Frame(lf_leg)
            f.pack(anchor=tk.W, padx=5, pady=1)
            tk.Canvas(f, width=14, height=14, bg=col, highlightthickness=1, highlightbackground="black").pack(side=tk.LEFT)
            ttk.Label(f, text=txt).pack(side=tk.LEFT, padx=5)

        self.lbl_stats = ttk.Label(ctrl, text="", font=("Arial", 9, "bold"), justify=tk.LEFT)
        self.lbl_stats.pack(pady=5, padx=5, anchor=tk.W)

    def load_preset_maze(self, n):
        n = max(10, min(20, int(n)))
        self.grid_size.set(n)
        self.grid_data = [[0 for _ in range(n)] for _ in range(n)]
        self.wave_matrix = [[None for _ in range(n)] for _ in range(n)]

        self.start_pos = (1, 1)
        self.goal_pos = (n - 2, n - 2)

        # Фіксований детермінований рисунок перешкод (-1)
        for i in range(n):
            # Зовнішні межі не обов'язкові, але зробимо внутрішні коридори
            if 2 <= i <= n - 4:
                self.grid_data[i][n // 3] = -1
            if 3 <= i <= n - 2:
                self.grid_data[i][(2 * n) // 3] = -1
            if 2 <= i <= n // 2:
                self.grid_data[n // 2][i] = -1

        # Додаткові перешкоди з проходами для діагоналей і ортогоналей
        self.grid_data[n // 3][n // 3] = 0
        self.grid_data[(2 * n) // 3][(2 * n) // 3] = 0
        self.grid_data[self.start_pos[0]][self.start_pos[1]] = 0
        self.grid_data[self.goal_pos[0]][self.goal_pos[1]] = 0

        self.draw_maze()

    def clear_walls(self):
        n = self.grid_size.get()
        self.grid_data = [[0 for _ in range(n)] for _ in range(n)]
        self.reset_wave_view()

    def add_more_obstacles(self):
        n = self.grid_size.get()
        # Детерміноване ущільнення перешкод (шахові бар'єри)
        for r in range(1, n - 1, 2):
            for c in range(2, n - 1, 3):
                if (r, c) != self.start_pos and (r, c) != self.goal_pos:
                    self.grid_data[r][c] = -1
        self.reset_wave_view()

    def swap_start_goal(self):
        self.start_pos, self.goal_pos = self.goal_pos, self.start_pos
        self.reset_wave_view()

    def reset_wave_view(self):
        n = self.grid_size.get()
        self.wave_matrix = [[None for _ in range(n)] for _ in range(n)]
        self.draw_maze()

    def on_canvas_click(self, event):
        n = self.grid_size.get()
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        cell_sz = min(w, h) // (n + 1)
        offset_x = (w - cell_sz * n) // 2
        offset_y = (h - cell_sz * n) // 2

        c = (event.x - offset_x) // cell_sz
        r = (event.y - offset_y) // cell_sz

        if 0 <= r < n and 0 <= c < n:
            mode = self.edit_mode.get()
            if mode == 0:
                if (r, c) != self.start_pos and (r, c) != self.goal_pos:
                    self.grid_data[r][c] = 0 if self.grid_data[r][c] == -1 else -1
            elif mode == 1:
                if (r, c) != self.goal_pos and self.grid_data[r][c] == 0:
                    self.start_pos = (r, c)
            elif mode == 2:
                if (r, c) != self.start_pos and self.grid_data[r][c] == 0:
                    self.goal_pos = (r, c)
            self.reset_wave_view()

    def on_canvas_drag(self, event):
        if self.edit_mode.get() == 0:
            n = self.grid_size.get()
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            cell_sz = min(w, h) // (n + 1)
            offset_x = (w - cell_sz * n) // 2
            offset_y = (h - cell_sz * n) // 2
            c = (event.x - offset_x) // cell_sz
            r = (event.y - offset_y) // cell_sz
            if 0 <= r < n and 0 <= c < n and (r, c) != self.start_pos and (r, c) != self.goal_pos:
                self.grid_data[r][c] = -1
                self.reset_wave_view()

    def draw_maze(self, front_set=None, path_set=None):
        self.canvas.delete("all")
        if front_set is None:
            front_set = set()
        if path_set is None:
            path_set = set()

        n = self.grid_size.get()
        w = max(800, self.canvas.winfo_width())
        h = max(760, self.canvas.winfo_height())
        cell_sz = min(w, h) // (n + 1)
        offset_x = (w - cell_sz * n) // 2
        offset_y = (h - cell_sz * n) // 2

        passable_cnt = 0
        wall_cnt = 0

        for r in range(n):
            for c in range(n):
                x1 = offset_x + c * cell_sz
                y1 = offset_y + r * cell_sz
                x2 = x1 + cell_sz
                y2 = y1 + cell_sz

                val = self.grid_data[r][c]
                w_val = self.wave_matrix[r][c]

                if val == -1:
                    wall_cnt += 1
                    bg_col = "#37474F"
                    fg_col = "#ECEFF1"
                    txt = "-1"
                else:
                    passable_cnt += 1
                    bg_col = "#FFFFFF"
                    fg_col = "#212121"
                    txt = "0"

                    if w_val is not None:
                        bg_col = "#B3E5FC"
                        txt = f"{w_val}"
                    if (r, c) in front_set:
                        bg_col = "#FFF176"
                    if (r, c) in path_set:
                        bg_col = "#66BB6A"
                        fg_col = "#FFFFFF"
                    if (r, c) == self.start_pos:
                        bg_col = "#FF8A65"
                        txt = f"S(0)" if w_val is not None else "S(0)"
                    elif (r, c) == self.goal_pos:
                        bg_col = "#FF7043"
                        txt = f"G({w_val})" if w_val is not None else "G(0)"

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=bg_col, outline="#90A4AE", width=1)
                # Підпис координати у кутку клітинки та значення в центрі
                self.canvas.create_text(x1 + 14, y1 + 8, text=f"{r},{c}", font=("Arial", 7), fill="#78909C")
                self.canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2 + 3, text=txt,
                                        font=("Consolas", 10, "bold"), fill=fg_col)

        # Відображення стрілки знайденого шляху поверх клітинок
        if len(path_set) > 1 and hasattr(self, 'last_ordered_path'):
            pts = []
            for r, c in self.last_ordered_path:
                cx = offset_x + c * cell_sz + cell_sz // 2
                cy = offset_y + r * cell_sz + cell_sz // 2
                pts.extend([cx, cy])
            if len(pts) >= 4:
                self.canvas.create_line(*pts, fill="#1B5E20", width=3, arrow=tk.LAST)

        total = n * n
        ratio_pass = (passable_cnt / total) * 100
        ratio_wall = (wall_cnt / total) * 100
        self.lbl_stats.config(
            text=f"Матриця: {n}x{n} (Всього {total} клітинок)\n"
                 f"Прохідних (0): {passable_cnt} ({ratio_pass:.1f}%) | Непрохідних (-1): {wall_cnt} ({ratio_wall:.1f}%)\n"
                 f"Старт S: {self.start_pos} | Мета G: {self.goal_pos}"
        )
        self.root.update()

    def get_deltas(self, op_type):
        if op_type == 0:
            # Вверх-вниз-вправо-вліво
            return [(-1, 0), (1, 0), (0, 1), (0, -1)]
        elif op_type == 1:
            # Тільки по діагоналях
            return [(-1, -1), (-1, 1), (1, 1), (1, -1)]
        else:
            # Комбінація (8 напрямків)
            return [(-1, 0), (1, 0), (0, 1), (0, -1), (-1, -1), (-1, 1), (1, 1), (1, -1)]

    def execute_wave_algorithm(self, op_type, animate=True):
        n = self.grid_size.get()
        w_mat = [[None for _ in range(n)] for _ in range(n)]
        deltas = self.get_deltas(op_type)

        sr, sc = self.start_pos
        gr, gc = self.goal_pos

        w_mat[sr][sc] = 0
        current_front = [(sr, sc)]
        expanded_count = 1
        wave_cycles = 0
        found = (sr == gr and sc == gc)

        t0 = time.perf_counter()

        # ЕТАП 1: Поширення хвилі (фронт за фронтом)
        while current_front and not found:
            wave_cycles += 1
            next_front = []
            for r, c in current_front:
                d = w_mat[r][c]
                for dr, dc in deltas:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n:
                        if self.grid_data[nr][nc] == 0 and w_mat[nr][nc] is None:
                            w_mat[nr][nc] = d + 1
                            next_front.append((nr, nc))
                            expanded_count += 1
                            if (nr, nc) == (gr, gc):
                                found = True

            current_front = next_front
            if animate and self.anim_speed.get() > 0:
                self.wave_matrix = w_mat
                self.draw_maze(front_set=set(current_front))
                time.sleep(self.anim_speed.get())

        # ЕТАП 2: Відновлення найкоротшого шляху (зворотний хід від Мети до Старту)
        path = []
        if found:
            curr = (gr, gc)
            path.append(curr)
            while curr != (sr, sc):
                cr, cc = curr
                cd = w_mat[cr][cc]
                for dr, dc in deltas:
                    pr, pc = cr + dr, cc + dc
                    if 0 <= pr < n and 0 <= pc < n and w_mat[pr][pc] == cd - 1:
                        curr = (pr, pc)
                        path.append(curr)
                        break
            path.reverse()

        dt_ms = max(0.001, (time.perf_counter() - t0) * 1000.0 -
                    (wave_cycles * self.anim_speed.get() * 1000.0 if animate else 0))

        return found, path, wave_cycles, expanded_count, dt_ms, w_mat

    def run_wave_search(self):
        op = self.operator_type.get()
        found, path, cycles, expanded, dt_ms, w_mat = self.execute_wave_algorithm(op, animate=True)
        self.wave_matrix = w_mat
        self.last_ordered_path = path
        self.draw_maze(path_set=set(path))
        self.show_report_window(op, found, path, cycles, expanded, dt_ms)

    def show_report_window(self, op, found, path, cycles, expanded, dt_ms):
        win = tk.Toplevel(self.root)
        win.title("Результати одно-направленого хвильового пошуку")
        win.geometry("580x440")

        txt = tk.Text(win, font=("Consolas", 10), wrap=tk.WORD, padx=10, pady=10)
        txt.pack(fill=tk.BOTH, expand=True)

        op_names = [
            "«Вверх-вниз-вправо-вліво» (4 ортогональні напрямки)",
            "«Перехід по діагоналях» (4 діагональні напрямки)",
            "Комбінований оператор (8 напрямків)"
        ]
        n = self.grid_size.get()
        passable = sum(1 for r in range(n) for c in range(n) if self.grid_data[r][c] == 0)
        walls = n * n - passable

        out = "=== ЗВІТ: ОДНО-НАПРАВЛЕНИЙ ХВИЛЬОВИЙ ПОШУК ===\n\n"
        out += f"Розмірність матриці лабіринту: {n}x{n} ({n*n} вершин)\n"
        out += f"Прохідних (0): {passable} | Непрохідних (-1): {walls}\n"
        out += f"Оператор переходу: {op_names[op]}\n"
        out += f"Початкова вершина S: {self.start_pos} ➔ Цільова G: {self.goal_pos}\n"
        out += "-" * 54 + "\n"

        if found:
            out += f"СТАТУС: Найкоротший шлях УСПІШНО знайдено!\n"
            out += f"Довжина шляху (кроків хвилі): {len(path)-1}\n"
            out += f"Кількість вершин у шляху: {len(path)}\n"
            out += f"Вершини у знайденому шляху:\n  " + " ➔ ".join(str(p) for p in path) + "\n\n"
        else:
            out += "СТАТУС: Шлях НЕ ЗНАЙДЕНО (цільова вершина недосяжна для даного оператора).\n\n"

        out += f"Кількість циклів поширення хвилі (фронтів): {cycles}\n"
        out += f"Загальна кількість розкритих вершин: {expanded} (із {passable} прохідних)\n"
        out += f"Чистий час виконання пошуку: {dt_ms:.4f} мс\n"

        txt.insert(tk.END, out)
        txt.config(state=tk.DISABLED)

    def compare_operators(self):
        win = tk.Toplevel(self.root)
        win.title("Порівняння операторів переходу за однакових умов")
        win.geometry("700x520")

        txt = tk.Text(win, font=("Consolas", 10), wrap=tk.WORD, padx=10, pady=10)
        txt.pack(fill=tk.BOTH, expand=True)

        n = self.grid_size.get()
        passable = sum(1 for r in range(n) for c in range(n) if self.grid_data[r][c] == 0)
        walls = n * n - passable

        out = "=== ПОРІВНЯЛЬНИЙ АНАЛІЗ ОПЕРАТОРІВ ПЕРЕХОДУ ===\n"
        out += f"Лабіринт: {n}x{n} | Прохідних (0): {passable} | Непрохідних (-1): {walls}\n"
        out += f"Маршрут: S{self.start_pos} ➔ G{self.goal_pos}\n"
        out += "=" * 64 + "\n\n"

        op_names = [
            "1. Оператор «Вверх-вниз-вправо-вліво» (4 ортогональні)",
            "2. Оператор «Перехід по діагоналях» (4 діагональні)",
            "3. Комбінований оператор (8 напрямків)"
        ]

        for op_idx in range(3):
            found, path, cycles, expanded, dt_ms, _ = self.execute_wave_algorithm(op_idx, animate=False)
            out += f"▶ {op_names[op_idx]}:\n"
            if found:
                out += f"  • Статус: ЗНАЙДЕНО | Довжина шляху: {len(path)-1} кроків ({len(path)} вершин)\n"
                out += f"  • Траєкторія: {' ➔ '.join(str(p) for p in path)}\n"
            else:
                out += f"  • Статус: ШЛЯХ НЕ ЗНАЙДЕНО (недосяжна парність або заблоковано стінами)\n"
            out += f"  • Кількість циклів (фронтів хвилі): {cycles}\n"
            out += f"  • Кількість розкритих вершин: {expanded}\n"
            out += f"  • Час виконання: {dt_ms:.4f} мс\n"
            out += "-" * 64 + "\n"

        txt.insert(tk.END, out)
        txt.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = WaveSearchLab3App(root)
    root.mainloop()