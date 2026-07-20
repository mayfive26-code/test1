"""網站健康檢查 GUI - tkinter 桌面應用程式。"""

import os
import threading
import time
import tkinter as tk
from tkinter import font as tkfont, scrolledtext, ttk
from pathlib import Path
from urllib.parse import urlparse

from practice5 import OUTPUT_DIR, check_website

# ── 色彩與主題 ──────────────────────────────────────────────
COLOR_BG = "#0d1b2a"  # 深藍背景
COLOR_CARD = "#1b2838"  # 卡片背景
COLOR_PRIMARY = "#1e88e5"  # 青藍主色
COLOR_TEAL = "#00acc1"  # 青綠強調
COLOR_WHITE = "#e0e0e0"
COLOR_TEXT = "#cfd8dc"
COLOR_SUCCESS = "#66bb6a"
COLOR_WARNING = "#ffa726"
COLOR_DANGER = "#ef5350"
COLOR_BORDER = "#2c3e50"
COLOR_HOVER = "#1565c0"

FONT_FAMILY = "Segoe UI"


# ── 工具函式 ────────────────────────────────────────────────
def is_valid_url(url: str) -> str | None:
    """驗證 URL 格式，回傳錯誤訊息；若合法則回傳 None。"""
    url = url.strip()
    if not url:
        return "請輸入網址"
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return "網址必須以 http:// 或 https:// 開頭"
    if not parsed.netloc:
        return "網址格式不正確，請檢查是否遺漏主機名稱"
    return None


def is_valid_timeout(value: str) -> tuple[bool, str]:
    """驗證 timeout 輸入，回傳 (是否合法, 錯誤訊息或已處理數值)。"""
    try:
        t = int(value)
        if t < 1000:
            return False, "超時時間至少為 1000 毫秒（1 秒）"
        if t > 120000:
            return False, "超時時間不可超過 120000 毫秒（120 秒）"
        return True, str(t)
    except ValueError:
        return False, "超時時間必須為整數（毫秒）"


# ── 自訂 Card Frame ─────────────────────────────────────────
class Card(tk.Frame):
    """圓角卡片容器。"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLOR_CARD, highlightbackground=COLOR_BORDER, highlightthickness=1, **kwargs)
        self.pack_propagate(False)


# ── 主應用程式 ──────────────────────────────────────────────
class HealthCheckApp(tk.Tk):
    """網站健康檢查 tkinter 應用程式。"""

    def __init__(self):
        super().__init__()
        self.title("網站健康檢查")
        self.geometry("1200x760")
        self.minsize(1000, 680)
        self.configure(bg=COLOR_BG)

        self._running = False
        self._worker: threading.Thread | None = None

        self._setup_styles()
        self._build_ui()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── 樣式設定 ────────────────────────────────────────────
    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT, font=(FONT_FAMILY, 10))
        style.configure("Card.TLabel", background=COLOR_CARD, foreground=COLOR_TEXT, font=(FONT_FAMILY, 10))
        style.configure("Title.TLabel", background=COLOR_CARD, foreground=COLOR_TEAL, font=(FONT_FAMILY, 14, "bold"))
        style.configure("Value.TLabel", background=COLOR_CARD, foreground=COLOR_WHITE, font=(FONT_FAMILY, 11, "bold"))
        style.configure("Success.TLabel", background=COLOR_CARD, foreground=COLOR_SUCCESS, font=(FONT_FAMILY, 12, "bold"))
        style.configure("Warning.TLabel", background=COLOR_CARD, foreground=COLOR_WARNING, font=(FONT_FAMILY, 12, "bold"))
        style.configure("Danger.TLabel", background=COLOR_CARD, foreground=COLOR_DANGER, font=(FONT_FAMILY, 12, "bold"))

        style.configure("Primary.TButton", background=COLOR_PRIMARY, foreground=COLOR_WHITE, font=(FONT_FAMILY, 10, "bold"), borderwidth=0, focuscolor="none")
        style.map("Primary.TButton",
                  background=[("active", COLOR_HOVER), ("disabled", "#37474f")],
                  foreground=[("disabled", "#78909c")])

        style.configure("Secondary.TButton", background=COLOR_TEAL, foreground=COLOR_WHITE, font=(FONT_FAMILY, 10), borderwidth=0, focuscolor="none")
        style.map("Secondary.TButton",
                  background=[("active", "#00838f"), ("disabled", "#37474f")],
                  foreground=[("disabled", "#78909c")])

        style.configure("Outline.TButton", background=COLOR_CARD, foreground=COLOR_TEAL, font=(FONT_FAMILY, 10), borderwidth=1, focuscolor="none")
        style.map("Outline.TButton",
                  background=[("active", COLOR_BORDER)],
                  foreground=[("active", COLOR_WHITE)])

        style.configure("TEntry", fieldbackground="#263238", foreground=COLOR_WHITE, insertcolor=COLOR_WHITE, borderwidth=1, font=(FONT_FAMILY, 10))
        style.map("TEntry",
                  fieldbackground=[("focus", "#2c3e50")])

        style.configure("TCombobox", fieldbackground="#263238", foreground=COLOR_WHITE, arrowcolor=COLOR_WHITE, borderwidth=1, font=(FONT_FAMILY, 10))
        style.map("TCombobox",
                  fieldbackground=[("focus", "#2c3e50")],
                  foreground=[("active", COLOR_WHITE)])

        style.configure("TCheckbutton", background=COLOR_BG, foreground=COLOR_TEXT, font=(FONT_FAMILY, 10))
        style.map("TCheckbutton",
                  background=[("active", COLOR_BG)],
                  foreground=[("active", COLOR_WHITE)])

        style.configure("TFrame", background=COLOR_BG)

    # ── UI 建置 ─────────────────────────────────────────────
    def _build_ui(self):
        # 頂部標題列
        header = tk.Frame(self, bg=COLOR_BG, height=50)
        header.pack(fill="x", padx=20, pady=(15, 5))
        header.pack_propagate(False)

        title_lbl = tk.Label(header, text="網站健康檢查", fg=COLOR_TEAL, bg=COLOR_BG,
                             font=(FONT_FAMILY, 20, "bold"))
        title_lbl.pack(side="left")

        subtitle_lbl = tk.Label(header, text="Website Health Check", fg="#546e7a", bg=COLOR_BG,
                                font=(FONT_FAMILY, 10))
        subtitle_lbl.pack(side="left", padx=(10, 0), pady=(8, 0))

        # 主內容左右雙欄
        main = tk.Frame(self, bg=COLOR_BG)
        main.pack(fill="both", expand=True, padx=20, pady=(5, 10))

        # ── 左欄 ────────────────────────────────────────────
        left_frame = tk.Frame(main, bg=COLOR_BG, width=340)
        left_frame.pack(side="left", fill="y", padx=(0, 10))
        left_frame.pack_propagate(False)

        # 參數設定卡片
        self._build_input_card(left_frame)

        # ── 右欄 ────────────────────────────────────────────
        right_frame = tk.Frame(main, bg=COLOR_BG)
        right_frame.pack(side="left", fill="both", expand=True)

        self._build_result_card(right_frame)

        # ── 底部日誌列 ──────────────────────────────────────
        self._build_log_area(self)

    # ── 輸入卡片 ────────────────────────────────────────────
    def _build_input_card(self, parent):
        card = Card(parent, height=520)
        card.pack(fill="x", pady=(0, 10))

        title = ttk.Label(card, text="⚙ 檢查設定", style="Title.TLabel")
        title.pack(anchor="w", padx=15, pady=(15, 10))

        # URL
        url_lbl = ttk.Label(card, text="目標網址", style="Card.TLabel")
        url_lbl.pack(anchor="w", padx=15, pady=(5, 2))

        self.url_var = tk.StringVar(value="https://example.com/")
        url_entry = ttk.Entry(card, textvariable=self.url_var, width=40)
        url_entry.pack(fill="x", padx=15, pady=(0, 8))

        # 瀏覽器
        browser_lbl = ttk.Label(card, text="瀏覽器", style="Card.TLabel")
        browser_lbl.pack(anchor="w", padx=15, pady=(5, 2))

        self.browser_var = tk.StringVar(value="chromium")
        browser_combo = ttk.Combobox(card, textvariable=self.browser_var,
                                     values=["chromium", "firefox", "webkit"],
                                     state="readonly", width=38)
        browser_combo.pack(fill="x", padx=15, pady=(0, 8))

        # Headless
        self.headless_var = tk.BooleanVar(value=True)
        headless_cb = ttk.Checkbutton(card, text="無頭模式（不顯示瀏覽器視窗）",
                                      variable=self.headless_var)
        headless_cb.pack(anchor="w", padx=15, pady=(5, 8))

        # Timeout
        timeout_lbl = ttk.Label(card, text="超時時間（毫秒）", style="Card.TLabel")
        timeout_lbl.pack(anchor="w", padx=15, pady=(5, 2))

        self.timeout_var = tk.StringVar(value="30000")
        timeout_entry = ttk.Entry(card, textvariable=self.timeout_var, width=40)
        timeout_entry.pack(fill="x", padx=15, pady=(0, 8))

        # 開始檢查按鈕
        self.check_btn = ttk.Button(card, text="▶ 開始檢查", style="Primary.TButton",
                                    command=self._start_check)
        self.check_btn.pack(fill="x", padx=15, pady=(15, 5))

        # 狀態提示
        self.status_lbl = ttk.Label(card, text="就緒", style="Card.TLabel")
        self.status_lbl.pack(anchor="w", padx=15, pady=(5, 10))

    # ── 結果卡片 ────────────────────────────────────────────
    def _build_result_card(self, parent):
        card = Card(parent, height=520)
        card.pack(fill="both", expand=True, pady=(0, 10))

        title = ttk.Label(card, text="📊 檢查結果", style="Title.TLabel")
        title.pack(anchor="w", padx=15, pady=(15, 10))

        # 結果網格
        grid = tk.Frame(card, bg=COLOR_CARD)
        grid.pack(fill="x", padx=15, pady=(0, 10))

        self._add_result_row(grid, "HTTP 狀態", 0)
        self.status_value = self._result_label(grid, 0)

        self._add_result_row(grid, "回應時間", 1)
        self.time_value = self._result_label(grid, 1)

        self._add_result_row(grid, "頁面標題", 2)
        self.title_value = self._result_label(grid, 2)

        self._add_result_row(grid, "最終 URL", 3)
        self.final_url_value = self._result_label(grid, 3)

        self._add_result_row(grid, "主標題", 4)
        self.heading_value = self._result_label(grid, 4)

        # 整體狀態
        status_frame = tk.Frame(card, bg=COLOR_CARD)
        status_frame.pack(fill="x", padx=15, pady=(5, 10))

        state_lbl = ttk.Label(status_frame, text="整體狀態", style="Card.TLabel")
        state_lbl.pack(side="left", padx=(0, 10))

        self.state_value = ttk.Label(status_frame, text="—", style="Card.TLabel")
        self.state_value.pack(side="left")

        # 截圖預覽
        preview_frame = tk.Frame(card, bg=COLOR_CARD)
        preview_frame.pack(fill="both", expand=True, padx=15, pady=(5, 10))

        preview_lbl = ttk.Label(preview_frame, text="截圖預覽", style="Card.TLabel")
        preview_lbl.pack(anchor="w")

        self.screenshot_canvas = tk.Canvas(preview_frame, bg="#141e28",
                                           highlightthickness=1,
                                           highlightbackground=COLOR_BORDER,
                                           height=200)
        self.screenshot_canvas.pack(fill="both", expand=True, pady=(5, 0))

        # 放置預設文字
        self.screenshot_canvas.create_text(
            10, 10, anchor="nw", text="尚未執行檢查，暫無截圖",
            fill="#546e7a", font=(FONT_FAMILY, 10)
        )

    @staticmethod
    def _add_result_row(parent, text, row):
        lbl = tk.Label(parent, text=text, fg=COLOR_TEXT, bg=COLOR_CARD,
                       font=(FONT_FAMILY, 10), anchor="w", width=12)
        lbl.grid(row=row, column=0, sticky="w", pady=3)

    @staticmethod
    def _result_label(parent, row):
        lbl = tk.Label(parent, text="—", fg=COLOR_WHITE, bg=COLOR_CARD,
                       font=(FONT_FAMILY, 10, "bold"), anchor="w")
        lbl.grid(row=row, column=1, sticky="w", pady=3, padx=(5, 0))
        return lbl

    # ── 底部日誌區 ──────────────────────────────────────────
    def _build_log_area(self, parent):
        log_frame = tk.Frame(parent, bg=COLOR_BG, height=180)
        log_frame.pack(fill="x", padx=20, pady=(0, 10))
        log_frame.pack_propagate(False)

        log_header = tk.Frame(log_frame, bg=COLOR_BG)
        log_header.pack(fill="x")

        log_title = tk.Label(log_header, text="📝 執行日誌", fg=COLOR_TEAL,
                             bg=COLOR_BG, font=(FONT_FAMILY, 11, "bold"))
        log_title.pack(side="left")

        btn_frame = tk.Frame(log_header, bg=COLOR_BG)
        btn_frame.pack(side="right")

        open_btn = ttk.Button(btn_frame, text="📂 開啟輸出資料夾",
                              style="Secondary.TButton",
                              command=self._open_output_dir)
        open_btn.pack(side="left", padx=(0, 5))

        clear_btn = ttk.Button(btn_frame, text="🗑 清除結果",
                               style="Outline.TButton",
                               command=self._clear_results)
        clear_btn.pack(side="left")

        self.log_text = scrolledtext.ScrolledText(
            log_frame, bg="#141e28", fg="#b0bec5",
            font=("Consolas", 9), wrap="word",
            highlightthickness=1, highlightbackground=COLOR_BORDER,
            borderwidth=0, height=8
        )
        self.log_text.pack(fill="both", expand=True, pady=(5, 0))

    # ── 按鈕回呼 ────────────────────────────────────────────
    def _open_output_dir(self):
        path = OUTPUT_DIR.resolve()
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        os.startfile(path)

    def _clear_results(self):
        self.status_value.config(text="—")
        self.time_value.config(text="—")
        self.title_value.config(text="—")
        self.final_url_value.config(text="—")
        self.heading_value.config(text="—")
        self.state_value.config(text="—", style="Card.TLabel")
        self.screenshot_canvas.delete("all")
        self.screenshot_canvas.create_text(
            10, 10, anchor="nw", text="尚未執行檢查，暫無截圖",
            fill="#546e7a", font=(FONT_FAMILY, 10)
        )
        self.log("結果已清除")

    def log(self, message: str):
        """向日誌區域新增一筆時間戳記訊息（可安全從任何執行緒呼叫）。"""
        timestamp = time.strftime("%H:%M:%S")
        self.after(0, lambda: self._append_log(f"[{timestamp}] {message}"))

    def _append_log(self, msg: str):
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")

    def _set_running(self, running: bool):
        self._running = running
        state = "disabled" if running else "normal"
        self.check_btn.config(state=state)
        if running:
            self.status_lbl.config(text="檢查中…", style="Warning.TLabel")
        else:
            self.status_lbl.config(text="就緒", style="Card.TLabel")

    # ── 背景工作 ────────────────────────────────────────────
    def _start_check(self):
        if self._running:
            return

        # 表單驗證
        url = self.url_var.get().strip()
        url_err = is_valid_url(url)
        if url_err:
            self._show_field_error(url_err)
            return

        timeout_str = self.timeout_var.get().strip()
        valid, msg = is_valid_timeout(timeout_str)
        if not valid:
            self._show_field_error(msg)
            return
        timeout = int(msg)

        self._set_running(True)
        self._worker = threading.Thread(
            target=self._run_check,
            args=(url, self.browser_var.get(), self.headless_var.get(), timeout),
            daemon=True,
        )
        self._worker.start()

    def _show_field_error(self, msg: str):
        self.status_lbl.config(text=msg, style="Danger.TLabel")
        self.log(f"⚠ 輸入錯誤: {msg}")

    def _run_check(self, url: str, browser: str, headless: bool, timeout: int):
        self.log(f"🔍 開始檢查: {url} (瀏覽器: {browser}, 無頭: {headless})")

        try:
            result = check_website(
                url=url,
                browser_name=browser,
                headless=headless,
                timeout=timeout,
            )
            self.log(f"✅ 檢查完成，狀態碼: {result.status}")
            self.after(0, self._update_result_ui, result)
        except Exception as e:
            self.log(f"❌ 檢查失敗: {e}")
            self.after(0, self._show_error, str(e))
        finally:
            self.after(0, lambda: self._set_running(False))

    def _update_result_ui(self, result):
        if result.error:
            self._show_error(result.error)
            return

        # HTTP 狀態
        status_text = str(result.status) if result.status else "無回應"
        self.status_value.config(text=status_text)

        # 回應時間
        self.time_value.config(text=f"{result.response_time_ms} ms")

        # 頁面標題
        self.title_value.config(text=result.page_title or "—")

        # 最終 URL
        self.final_url_value.config(text=result.final_url or "—")

        # 主標題
        self.heading_value.config(text=result.main_heading or "—")

        # 整體狀態
        if result.status and 200 <= result.status < 400:
            self.state_value.config(text="✅ 正常", style="Success.TLabel")
        elif result.status:
            self.state_value.config(text=f"⚠ 異常 ({result.status})", style="Warning.TLabel")
        else:
            self.state_value.config(text="❌ 無法連線", style="Danger.TLabel")

        # 截圖預覽
        self._show_screenshot(result.screenshot_path)

    def _show_screenshot(self, path: Path | None):
        self.screenshot_canvas.delete("all")
        w = self.screenshot_canvas.winfo_width()
        if w < 50:
            w = 400
        h = self.screenshot_canvas.winfo_height()
        if h < 50:
            h = 200

        if path and path.exists():
            try:
                from PIL import Image, ImageTk
                img = Image.open(path)
                img.thumbnail((w - 10, h - 10), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.screenshot_canvas.image = photo
                self.screenshot_canvas.create_image(w // 2, h // 2, image=photo, anchor="center")
            except ImportError:
                self.screenshot_canvas.create_text(
                    w // 2, h // 2, text=f"截圖已儲存：{path.name}\n（安裝 Pillow 可預覽）",
                    fill="#546e7a", font=(FONT_FAMILY, 10), justify="center"
                )
        else:
            self.screenshot_canvas.create_text(
                w // 2, h // 2, text="暫無截圖", fill="#546e7a",
                font=(FONT_FAMILY, 10)
            )

    def _show_error(self, error_msg: str):
        self.state_value.config(text="❌ 錯誤", style="Danger.TLabel")
        self.status_lbl.config(text="檢查失敗", style="Danger.TLabel")
        friendly = self._friendly_error(error_msg)
        self.log(f"❌ {friendly}")

    @staticmethod
    def _friendly_error(msg: str) -> str:
        """將 Playwright 錯誤訊息轉換為對學生友善的提示。"""
        msg_lower = msg.lower()
        if "timeout" in msg_lower and "30000" in msg:
            return "連線超時（30 秒）— 請檢查網址是否正確，或增加超時時間"
        if "timeout" in msg_lower:
            return f"等待超時 — {msg}"
        if "dns" in msg_lower or "err_name_not_resolved" in msg_lower:
            return "無法解析網域名稱 — 請檢查網址是否拼寫正確"
        if "connection refused" in msg_lower:
            return "連線被拒絕 — 目標網站可能未啟動或封鎖了連線"
        if "certificate" in msg_lower or "ssl" in msg_lower:
            return "SSL / 憑證錯誤 — 網站安全性設定可能有問題"
        if "404" in msg:
            return "找不到頁面（HTTP 404）— 請確認網址路徑是否正確"
        if "403" in msg:
            return "禁止存取（HTTP 403）— 網站可能封鎖了自動化工具"
        return f"發生錯誤: {msg}"

    def _on_close(self):
        self._running = False
        self.destroy()


# ── 程式進入點 ──────────────────────────────────────────────
def main():
    """啟動 GUI 應用程式（可從命令列執行 python gui.py）。"""
    app = HealthCheckApp()
    app.mainloop()


if __name__ == "__main__":
    main()
