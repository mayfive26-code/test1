import random
import tkinter as tk
from tkinter import messagebox


# ===== 色彩主題 =====
BG_COLOR = "#1e1e2e"
CARD_BG = "#313244"
ACCENT = "#89b4fa"
GREEN = "#a6e3a1"
RED = "#f38ba8"
YELLOW = "#f9e2af"
TEXT_WHITE = "#cdd6f4"
TEXT_DIM = "#a6adc8"
BTN_BG = "#45475a"
BTN_HOVER = "#585b70"


class GuessNumberGame:
    def __init__(self, root):
        self.root = root
        self.root.title("猜數字遊戲")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)

        self.target = random.randint(1, 100)
        self.low = 1
        self.high = 100
        self.attempts = 0
        self.max_attempts = 7  # 二分搜尋最多 7 次 (log2(100))

        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        container = tk.Frame(self.root, bg=BG_COLOR)
        container.pack(padx=30, pady=20)

        # ---- 標題 ----
        tk.Label(
            container, text="🎯 猜數字遊戲", font=("Microsoft JhengHei", 22, "bold"),
            bg=BG_COLOR, fg=ACCENT,
        ).pack(pady=(0, 4))
        tk.Label(
            container, text="1 ~ 100，看你幾次能猜中", font=("Microsoft JhengHei", 10),
            bg=BG_COLOR, fg=TEXT_DIM,
        ).pack(pady=(0, 16))

        # ---- 範圍顯示卡片 ----
        range_card = tk.Frame(container, bg=CARD_BG, highlightbackground=BTN_BG,
                              highlightthickness=1)
        range_card.pack(fill="x", pady=(0, 12))

        self.range_var = tk.StringVar(value="1 ~ 100")
        tk.Label(
            range_card, text="目前範圍", font=("Microsoft JhengHei", 9),
            bg=CARD_BG, fg=TEXT_DIM,
        ).pack(pady=(10, 0))
        tk.Label(
            range_card, textvariable=self.range_var,
            font=("Consolas", 26, "bold"), bg=CARD_BG, fg=YELLOW,
        ).pack(pady=(0, 10))

        # ---- 嘗試次數 ----
        stats_frame = tk.Frame(container, bg=BG_COLOR)
        stats_frame.pack(fill="x", pady=(0, 10))

        self.attempts_var = tk.StringVar(value="已猜：0 次")
        tk.Label(
            stats_frame, textvariable=self.attempts_var,
            font=("Microsoft JhengHei", 10), bg=BG_COLOR, fg=TEXT_DIM,
        ).pack(side="left")

        self.hint_var = tk.StringVar(value=f"最多 {self.max_attempts} 次可保證猜中")
        tk.Label(
            stats_frame, textvariable=self.hint_var,
            font=("Microsoft JhengHei", 10), bg=BG_COLOR, fg=TEXT_DIM,
        ).pack(side="right")

        # ---- 進度條（剩餘範圍比例）----
        progress_frame = tk.Frame(container, bg=BTN_BG, height=8)
        progress_frame.pack(fill="x", pady=(0, 14))
        progress_frame.pack_propagate(False)

        self.progress_bar = tk.Frame(progress_frame, bg=ACCENT, height=8)
        self.progress_bar.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)

        # ---- 輸入區 ----
        input_frame = tk.Frame(container, bg=CARD_BG, highlightbackground=BTN_BG,
                               highlightthickness=1)
        input_frame.pack(fill="x", pady=(0, 10))

        inner = tk.Frame(input_frame, bg=CARD_BG)
        inner.pack(padx=12, pady=12)

        tk.Label(
            inner, text="你的猜測", font=("Microsoft JhengHei", 10),
            bg=CARD_BG, fg=TEXT_DIM,
        ).pack(anchor="w")

        row = tk.Frame(inner, bg=CARD_BG)
        row.pack(fill="x", pady=(4, 0))

        self.entry = tk.Entry(
            row, width=8, font=("Consolas", 18, "bold"),
            bg=BG_COLOR, fg=TEXT_WHITE, insertbackground=TEXT_WHITE,
            highlightbackground=BTN_BG, highlightthickness=1,
            justify="center",
        )
        self.entry.pack(side="left", ipady=4)
        self.entry.bind("<Return>", lambda e: self._make_guess())

        self.guess_btn = tk.Button(
            row, text="猜!", font=("Microsoft JhengHei", 12, "bold"),
            bg=ACCENT, fg=BG_COLOR, activebackground=BTN_HOVER,
            relief="flat", cursor="hand2", padx=16, pady=4,
            command=self._make_guess,
        )
        self.guess_btn.pack(side="left", padx=(8, 0))

        # ---- 結果訊息 ----
        self.result_var = tk.StringVar(value="")
        self.result_label = tk.Label(
            container, textvariable=self.result_var,
            font=("Microsoft JhengHei", 13, "bold"),
            bg=BG_COLOR, fg=TEXT_WHITE, width=28,
        )
        self.result_label.pack(pady=(2, 10))

        # ---- 猜測紀錄 ----
        record_header = tk.Frame(container, bg=BG_COLOR)
        record_header.pack(fill="x")
        tk.Label(
            record_header, text="📝 猜測紀錄", font=("Microsoft JhengHei", 10, "bold"),
            bg=BG_COLOR, fg=TEXT_DIM,
        ).pack(anchor="w")

        self.history_listbox = tk.Listbox(
            container, font=("Microsoft JhengHei", 10),
            bg=CARD_BG, fg=TEXT_WHITE, selectbackground=BTN_BG,
            highlightbackground=BTN_BG, highlightthickness=1,
            borderwidth=0, height=7, activestyle="none",
        )
        self.history_listbox.pack(fill="x", pady=(6, 12))

        # ---- 底部按鈕 ----
        btn_frame = tk.Frame(container, bg=BG_COLOR)
        btn_frame.pack(fill="x")

        self.restart_btn = tk.Button(
            btn_frame, text="🔄 重新開始", font=("Microsoft JhengHei", 10),
            bg=BTN_BG, fg=TEXT_WHITE, activebackground=BTN_HOVER,
            relief="flat", cursor="hand2", padx=12, pady=4,
            command=self._restart,
        )
        self.restart_btn.pack(side="left")

        self.quit_btn = tk.Button(
            btn_frame, text="✕ 離開", font=("Microsoft JhengHei", 10),
            bg=BTN_BG, fg=RED, activebackground=BTN_HOVER,
            relief="flat", cursor="hand2", padx=12, pady=4,
            command=self.root.quit,
        )
        self.quit_btn.pack(side="right")

        # 初始焦點
        self.entry.focus_set()

    # ------------------------------------------------------------------ 邏輯
    def _make_guess(self):
        raw = self.entry.get().strip()
        if not raw:
            self._show_result("請輸入一個數字", RED)
            return

        try:
            guess = int(raw)
        except ValueError:
            self._show_result("請輸入有效的整數", RED)
            return

        if guess < self.low or guess > self.high:
            self._show_result(f"超出範圍！({self.low} ~ {self.high})", RED)
            return

        self.attempts += 1
        self.entry.delete(0, tk.END)
        self.attempts_var.set(f"已猜：{self.attempts} 次")

        if guess == self.target:
            self._show_result(f"🎉 答對了！答案就是 {self.target}", GREEN)
            record = f"  第{self.attempts}次：{guess}  ✅ 答對！"
            self.history_listbox.insert(tk.END, record)
            self.history_listbox.itemconfig(tk.END, fg=GREEN)
            self._end_game()
        elif guess < self.target:
            self.low = guess + 1
            self._show_result("⬆ 太小了，往大一點猜", YELLOW)
            record = f"  第{self.attempts}次：{guess}  ⬆ 太小"
            self.history_listbox.insert(tk.END, record)
            self.history_listbox.itemconfig(tk.END, fg=YELLOW)
        else:
            self.high = guess - 1
            self._show_result("⬇ 太大了，往小一點猜", YELLOW)
            record = f"  第{self.attempts}次：{guess}  ⬇ 太大"
            self.history_listbox.insert(tk.END, record)
            self.history_listbox.itemconfig(tk.END, fg=YELLOW)

        self.range_var.set(f"{self.low}  ~  {self.high}")
        self._update_progress()
        self.history_listbox.see(tk.END)

    def _update_progress(self):
        """根據剩餘範圍更新進度條寬度"""
        total = 100
        remaining = self.high - self.low + 1
        ratio = remaining / total
        self.progress_bar.place(relx=0, rely=0, relwidth=max(ratio, 0.01), relheight=1.0)

        if ratio <= 0.1:
            self.progress_bar.configure(bg=GREEN)
        elif ratio <= 0.3:
            self.progress_bar.configure(bg=YELLOW)
        else:
            self.progress_bar.configure(bg=ACCENT)

    def _show_result(self, msg, color):
        self.result_var.set(msg)
        self.result_label.configure(fg=color)

    def _end_game(self):
        self.entry.config(state=tk.DISABLED)
        self.guess_btn.config(state=tk.DISABLED, bg=BTN_BG)

    def _restart(self):
        self.target = random.randint(1, 100)
        self.low = 1
        self.high = 100
        self.attempts = 0

        self.entry.config(state=tk.NORMAL)
        self.entry.delete(0, tk.END)
        self.guess_btn.config(state=tk.NORMAL, bg=ACCENT)

        self.range_var.set("1  ~  100")
        self.attempts_var.set("已猜：0 次")
        self._show_result("", TEXT_WHITE)
        self.history_listbox.delete(0, tk.END)
        self.progress_bar.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
        self.progress_bar.configure(bg=ACCENT)
        self.entry.focus_set()


if __name__ == "__main__":
    root = tk.Tk()
    game = GuessNumberGame(root)
    root.mainloop()
