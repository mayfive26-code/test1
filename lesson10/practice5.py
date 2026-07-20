"""專案 01：開啟真實網頁，檢查標題並留下截圖。"""
# 以上為此程式的文件字串，說明這個專案的目的：開啟真實網頁、檢查標題並截圖。

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

# 設定目標網址與截圖輸出目錄
URL = "https://example.com/"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def check_website(browser_name: str = "chromium") -> None:
    """使用指定的瀏覽器開啟網頁，檢查標題並進行截圖。"""
    # 確保輸出目錄存在（若不存在則建立）
    OUTPUT_DIR.mkdir(exist_ok=True)

    # 啟動 Playwright 並操作瀏覽器
    with sync_playwright() as playwright:
        # 根據參數取得對應的瀏覽器類型（chromium / firefox / webkit）
        browser_type = getattr(playwright, browser_name)
        # 以無頭模式啟動瀏覽器（不顯示視窗）
        browser = browser_type.launch(headless=True)
        # 建立新頁面，設定解析度為 1280x720
        page = browser.new_page(viewport={"width": 1280, "height": 720})

        # 導航到目標網址，等待 DOM 內容載入完成
        response = page.goto(URL, wait_until="domcontentloaded")
        # 取得頁面中 role="heading" 且名稱為 "Example Domain" 的元素文字
        heading = page.get_by_role("heading", name="Example Domain").inner_text()
        # 設定截圖檔案路徑
        screenshot = OUTPUT_DIR / f"homepage_{browser_name}.png"
        # 拍攝全頁截圖並儲存
        page.screenshot(path=screenshot, full_page=True)

        # 輸出結果資訊
        print(f"瀏覽器: {browser_name}")
        print(f"HTTP 狀態: {response.status if response else '無回應'}")
        print(f"頁面標題: {page.title()}")
        print(f"主標題: {heading}")
        print(f"截圖: {screenshot}")
        # 關閉瀏覽器
        browser.close()


if __name__ == "__main__":
    # 解析命令列引數：可指定 --browser，預設為 chromium
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--browser", choices=["chromium", "firefox", "webkit"], default="chromium"
    )
    args = parser.parse_args()
    # 執行檢查
    check_website(args.browser)
