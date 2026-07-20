"""專案 01：開啟真實網頁，檢查標題並留下截圖。"""

import argparse
import time
from dataclasses import dataclass, field
from pathlib import Path

from playwright.sync_api import sync_playwright


# 設定目標網址與截圖輸出目錄
URL = "https://example.com/"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


@dataclass
class WebsiteCheckResult:
    """網站健康檢查的結果資料。"""

    url: str
    browser: str
    headless: bool
    timeout: int
    status: int | None = None
    response_time_ms: float = 0.0
    page_title: str = ""
    main_heading: str = ""
    final_url: str = ""
    screenshot_path: Path | None = None
    error: str = ""
    timestamp: float = field(default_factory=time.time)


def check_website(
    url: str = URL,
    browser_name: str = "chromium",
    headless: bool = True,
    timeout: int = 30000,
) -> WebsiteCheckResult:
    """使用 Playwright 開啟目標網頁，回傳檢查結果（不輸出任何內容）。"""
    result = WebsiteCheckResult(url=url, browser=browser_name, headless=headless, timeout=timeout)

    OUTPUT_DIR.mkdir(exist_ok=True)

    start = time.perf_counter()
    try:
        with sync_playwright() as playwright:
            browser_type = getattr(playwright, browser_name)
            browser = browser_type.launch(headless=headless, timeout=timeout)
            page = browser.new_page(viewport={"width": 1280, "height": 720})

            response = page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            elapsed = (time.perf_counter() - start) * 1000
            result.response_time_ms = round(elapsed, 1)

            if response:
                result.status = response.status
                result.final_url = response.url
            result.page_title = page.title()
            result.main_heading = page.get_by_role("heading").first.inner_text()

            screenshot = OUTPUT_DIR / f"homepage_{browser_name}.png"
            page.screenshot(path=screenshot, full_page=True)
            result.screenshot_path = screenshot

            browser.close()
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        result.response_time_ms = round(elapsed, 1)
        result.error = str(e)

    return result


def print_result(result: WebsiteCheckResult) -> None:
    """將 WebsiteCheckResult 輸出到終端機（供 CLI 使用）。"""
    print(f"瀏覽器: {result.browser}")
    if result.error:
        print(f"錯誤: {result.error}")
    else:
        print(f"HTTP 狀態: {result.status if result.status else '無回應'}")
        print(f"回應時間: {result.response_time_ms} ms")
        print(f"頁面標題: {result.page_title}")
        print(f"主標題: {result.main_heading}")
        print(f"最終 URL: {result.final_url}")
        print(f"截圖: {result.screenshot_path}")


def main() -> None:
    """命令列入口：解析引數並執行網站檢查。"""
    parser = argparse.ArgumentParser(description="網站健康檢查工具")
    parser.add_argument("--url", default=URL, help="目標網址")
    parser.add_argument(
        "--browser",
        choices=["chromium", "firefox", "webkit"],
        default="chromium",
        help="瀏覽器類型",
    )
    parser.add_argument("--timeout", type=int, default=30000, help="等待超時（毫秒）")
    parser.add_argument(
        "--no-headless",
        action="store_false",
        dest="headless",
        help="顯示瀏覽器視窗（預設為無頭模式）",
    )
    args = parser.parse_args()

    result = check_website(
        url=args.url,
        browser_name=args.browser,
        headless=args.headless,
        timeout=args.timeout,
    )
    print_result(result)


if __name__ == "__main__":
    main()
