"""
維基百科爬蟲 Gradio 介面
美觀好用的 Wikipedia 搜尋工具
"""

import os
import traceback
import gradio as gr
from datetime import datetime
from playwright.sync_api import sync_playwright, Playwright, Browser, Page


def crawl_wikipedia(keyword: str, headless: bool = True) -> tuple:
    """
    維基百科爬蟲主函式

    Args:
        keyword: 搜尋關鍵字
        headless: 是否使用無頭模式

    Returns:
        (heading, summary, screenshot_path, status)
    """
    if not keyword or not keyword.strip():
        return "", "", None, "請輸入搜尋關鍵字"

    try:
        with sync_playwright() as p:
            browser: Browser = p.chromium.launch(headless=headless)
            try:
                page: Page = browser.new_page()
                page.set_default_timeout(60000)

                print(f"[DEBUG] 前往維基百科...")
                page.goto("https://zh.wikipedia.org", wait_until="domcontentloaded")
                page.wait_for_timeout(2000)

                print(f"[DEBUG] 搜尋關鍵字: {keyword}")
                search_input = page.locator("#searchInput")
                search_input.wait_for(state="visible", timeout=10000)
                search_input.fill(keyword.strip())
                page.wait_for_timeout(500)

                print(f"[DEBUG] 點擊搜尋按鈕...")
                search_btn = page.locator("button#searchGoButton, button.oo-ui-inputWidget-input")
                if search_btn.count() > 0:
                    search_btn.first.click()
                else:
                    page.keyboard.press("Enter")

                print(f"[DEBUG] 等待頁面載入...")
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(3000)

                print(f"[DEBUG] 取得頁面標題...")
                heading = ""
                try:
                    heading_el = page.locator("#firstHeading")
                    heading_el.wait_for(state="visible", timeout=10000)
                    heading = heading_el.inner_text()
                except Exception as e:
                    print(f"[DEBUG] 取得標題失敗: {e}")
                    heading = page.title()

                print(f"[DEBUG] 取得頁面內容...")
                content = ""
                try:
                    content_el = page.locator("#mw-content-text")
                    content_el.wait_for(state="visible", timeout=10000)
                    
                    paragraphs = page.locator("#mw-content-text p")
                    if paragraphs.count() > 0:
                        content = paragraphs.first.inner_text()
                except Exception as e:
                    print(f"[DEBUG] 取得內容失敗: {e}")
                    content = "無法取得頁面內容"

                if len(content) > 300:
                    content = content[:300] + "..."

                print(f"[DEBUG] 截圖...")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"screenshot_{timestamp}.png"
                page.screenshot(path=screenshot_path, full_page=False)
                print(f"[DEBUG] 截圖已儲存: {screenshot_path}")

                status_msg = f"搜尋完成: {keyword}"
                print(f"[DEBUG] {status_msg}")

                return heading, content, screenshot_path, status_msg

            finally:
                browser.close()

    except Exception as e:
        error_msg = f"搜尋失敗: {str(e)}"
        print(f"[ERROR] {error_msg}")
        print(traceback.format_exc())
        return "", "", None, error_msg


def clear_all():
    """清除所有欄位"""
    return "", "", "", "等待輸入...", None


CSS = """
.gradio-container {
    max-width: 900px !important;
    margin: auto !important;
}

.main-title {
    text-align: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.5em;
    font-weight: bold;
    margin-bottom: 10px;
}

.subtitle {
    text-align: center;
    color: #666;
    font-size: 1.1em;
    margin-bottom: 20px;
}

footer {
    display: none !important;
}
"""

with gr.Blocks(
    css=CSS,
    title="維基百科爬蟲",
    theme=gr.themes.Soft(
        primary_hue="indigo",
        secondary_hue="purple",
    ),
) as demo:
    gr.HTML('<div class="main-title">維基百科爬蟲工具</div>')
    gr.HTML('<div class="subtitle">輸入關鍵字，自動搜尋維基百科並擷取摘要</div>')

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 搜尋設定")
            keyword_input = gr.Textbox(
                label="搜尋關鍵字",
                placeholder="請輸入想搜尋的內容...",
                value="臺灣",
                lines=1,
            )

            with gr.Row():
                search_btn = gr.Button(
                    "開始搜尋",
                    variant="primary",
                    size="lg",
                )
                clear_btn = gr.Button(
                    "清除",
                    variant="secondary",
                    size="lg",
                )

            headless_toggle = gr.Checkbox(
                label="無頭模式 (不顯示瀏覽器視窗)",
                value=True,
            )

            status_output = gr.Textbox(
                label="狀態",
                value="等待輸入...",
                interactive=False,
            )

        with gr.Column(scale=2):
            gr.Markdown("### 搜尋結果")
            heading_output = gr.Textbox(
                label="頁面標題",
                interactive=False,
                lines=1,
            )
            summary_output = gr.Textbox(
                label="內容摘要",
                interactive=False,
                lines=6,
            )
            screenshot_output = gr.Image(
                label="頁面截圖",
                height=400,
            )

    search_btn.click(
        fn=crawl_wikipedia,
        inputs=[keyword_input, headless_toggle],
        outputs=[heading_output, summary_output, screenshot_output, status_output],
    )

    clear_btn.click(
        fn=clear_all,
        outputs=[keyword_input, heading_output, summary_output, status_output, screenshot_output],
    )

    keyword_input.submit(
        fn=crawl_wikipedia,
        inputs=[keyword_input, headless_toggle],
        outputs=[heading_output, summary_output, screenshot_output, status_output],
    )

    gr.Markdown("---")
    gr.Markdown(
        """
        <div style="text-align: center; color: #888; font-size: 0.9em;">
        使用 Playwright + Gradio 製作 | 資料來源：維基百科
        </div>
        """
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
