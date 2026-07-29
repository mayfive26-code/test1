import sys
import json
import os
from datetime import datetime, QTime, QDate
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QDateEdit, QTimeEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QGraphicsDropShadowEffect,
    QSplitter, QScrollArea, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont, QColor, QIcon

# 匯入你原本的爬蟲與 Playwright 套件
from playwright.sync_api import sync_playwright
import crawler

# ----------------------------------------------------------------------
# 1. 車站清單定義
# ----------------------------------------------------------------------
STATIONS = [
    "南港", "台北", "板橋", "桃園", "新竹", "苗栗",
    "台中", "彰化", "雲林", "嘉義", "台南", "左營"
]
COOKIES_FILE = "thsrc_cookies.json"

# ----------------------------------------------------------------------
# 2. 後台爬蟲執行緒 (防止 UI 凍結卡死)
# ----------------------------------------------------------------------
class CrawlerThread(QThread):
    finished_signal = Signal(bool, str)

    def __init__(self, departure, arrival, date_str, time_str):
        super().__init__()
        self.departure = departure
        self.arrival = arrival
        self.date_str = date_str
        self.time_str = time_str

    def run(self):
        try:
            with sync_playwright() as p:
                # 這裡執行你原本寫好的 crawler.crawl
                # 建議：後續可以重構 crawler.py，讓 crawl 回傳 dict 格式資料以填入表格
                crawler.crawl(
                    p=p,
                    cookies_file=COOKIES_FILE,
                    headless=False,  # 若穩定後可改為 True
                    departure_station=self.departure,
                    arrival_station=self.arrival
                )
            self.finished_signal.emit(True, "查詢完成！")
        except Exception as e:
            self.finished_signal.emit(False, str(e))

# ----------------------------------------------------------------------
# 3. 主視窗 UI 設計
# ----------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("台灣高鐵時刻表查詢系統 THSRC Query System")
        self.resize(1280, 800)
        self.setMinimumSize(1100, 700)

        # 全域樣式表 (QSS)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F4F6F9;
            }
            QLabel {
                font-family: 'Segoe UI', 'Microsoft JhengHei', sans-serif;
                color: #2D3748;
            }
            QFrame#Card {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E2E8F0;
            }
            QComboBox, QDateEdit, QTimeEdit {
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                color: #1E293B;
                font-family: 'Microsoft JhengHei';
            }
            QComboBox:hover, QDateEdit:hover, QTimeEdit:hover {
                border-color: #FD7E14;
            }
            QComboBox:focus, QDateEdit:focus, QTimeEdit:focus {
                border-color: #FD7E14;
                background-color: #FFFFFF;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QPushButton#SearchBtn {
                background-color: #FD7E14;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 16px;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Microsoft JhengHei';
            }
            QPushButton#SearchBtn:hover {
                background-color: #E86B00;
            }
            QPushButton#SearchBtn:pressed {
                background-color: #C95B00;
            }
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                gridline-color: #EDF2F7;
                font-family: 'Microsoft JhengHei';
            }
            QHeaderView::section {
                background-color: #1E293B;
                color: #FFFFFF;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
        """)

        self._init_ui()

    def _init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(20)

        # ---- Header 標頭 ----
        header_layout = QHBoxLayout()
        title_label = QLabel("🚄 台灣高鐵時刻表查詢")
        title_font = QFont("Microsoft JhengHei", 20, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #0F172A;")

        subtitle_label = QLabel("Taiwan High Speed Rail Schedule")
        subtitle_label.setStyleSheet("color: #64748B; font-size: 13px; font-weight: 500;")

        header_title_box = QVBoxLayout()
        header_title_box.addWidget(title_label)
        header_title_box.addWidget(subtitle_label)

        header_layout.addLayout(header_title_box)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # ---- 控制面板卡片 (Search Card) ----
        search_card = QFrame()
        search_card.setObjectName("Card")
        self._add_shadow(search_card)

        search_layout = QHBoxLayout(search_card)
        search_layout.setContentsMargins(20, 20, 20, 20)
        search_layout.setSpacing(16)

        # 1. 出發站
        dep_box = QVBoxLayout()
        dep_box.addWidget(QLabel("出發站"))
        self.dep_combo = QComboBox()
        self.dep_combo.addItems(STATIONS)
        self.dep_combo.setCurrentText("台北")
        dep_box.addWidget(self.dep_combo)

        # 2. 到達站
        arr_box = QVBoxLayout()
        arr_box.addWidget(QLabel("到達站"))
        self.arr_combo = QComboBox()
        self.arr_combo.addItems(STATIONS)
        self.arr_combo.setCurrentText("台中")
        arr_box.addWidget(self.arr_combo)

        # 3. 日期選擇
        date_box = QVBoxLayout()
        date_box.addWidget(QLabel("出發日期"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy/MM/dd")
        date_box.addWidget(self.date_edit)

        # 4. 時間選擇
        time_box = QVBoxLayout()
        time_box.addWidget(QLabel("出發時間"))
        self.time_edit = QTimeEdit()
        # 預設為目前時間加 1 小時
        default_time = QTime.currentTime().addSecs(3600)
        self.time_edit.setTime(default_time)
        self.time_edit.setDisplayFormat("HH:mm")
        time_box.addWidget(self.time_edit)

        # 5. 查詢按鈕
        btn_box = QVBoxLayout()
        btn_box.addWidget(QLabel(""))  # 占位對齊
        self.search_btn = QPushButton("開始查詢")
        self.search_btn.setObjectName("SearchBtn")
        self.search_btn.setCursor(Qt.PointingHandCursor)
        self.search_btn.setFixedHeight(42)
        self.search_btn.clicked.connect(self._on_search_clicked)
        btn_box.addWidget(self.search_btn)

        # 將控制項加入卡片佈局
        search_layout.addLayout(dep_box, 2)
        search_layout.addLayout(arr_box, 2)
        search_layout.addLayout(date_box, 2)
        search_layout.addLayout(time_box, 2)
        search_layout.addLayout(btn_box, 2)

        main_layout.addWidget(search_card)

        # ---- 進度條 ----
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # 無限循環載入條
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: none; background-color: #E2E8F0; }
            QProgressBar::chunk { background-color: #FD7E14; }
        """)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # ---- 結果卡片 (Results Card) ----
        result_card = QFrame()
        result_card.setObjectName("Card")
        self._add_shadow(result_card)

        result_layout = QVBoxLayout(result_card)
        result_layout.setContentsMargins(16, 16, 16, 16)

        # 表格元件
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["出發時間", "行車時間", "抵達時間", "車次", "自由座車廂"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("alternate-background-color: #F8FAFC;")

        result_layout.addWidget(self.table)
        main_layout.addWidget(result_card, 1)

    def _add_shadow(self, widget: QWidget):
        """為元件新增柔和陰影"""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 15))
        widget.setGraphicsEffect(shadow)

    def _on_search_clicked(self):
        dep = self.dep_combo.currentText()
        arr = self.arr_combo.currentText()

        if dep == arr:
            QMessageBox.warning(self, "警告", "出發站與到達站不能相同！")
            return

        date_str = self.date_edit.date().toString("yyyy/MM/dd")
        time_str = self.time_edit.time().toString("HH:mm")

        # 啟用 UI 載入狀態
        self.search_btn.setEnabled(False)
        self.search_btn.setText("查詢中...")
        self.progress_bar.show()

        # 啟動非同步執行緒執行 Playwright
        self.thread = CrawlerThread(dep, arr, date_str, time_str)
        self.thread.finished_signal.connect(self._on_crawl_finished)
        self.thread.start()

    def _on_crawl_finished(self, success: bool, message: str):
        # 恢復 UI 狀態
        self.search_btn.setEnabled(True)
        self.search_btn.setText("開始查詢")
        self.progress_bar.hide()

        if success:
            QMessageBox.information(self, "成功", "爬蟲執行完成！(詳細輸出請參閱 Terminal)")
        else:
            QMessageBox.critical(self, "錯誤", f"查詢失敗：\n{message}")

# ----------------------------------------------------------------------
# 4. 主程式進入點
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 支援高 DPI 螢幕縮放
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
