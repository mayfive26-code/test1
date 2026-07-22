# Code Review: practice1.py

## 維基百科爬蟲練習 - 程式碼審查

---

## 概述

使用 Playwright 自動化瀏覽器，搜尋維基百科並擷取頁面資訊的爬蟲腳本。

---

## 優點

1. **類型提示完整** - 使用了型別註解（Type Hints），提升可讀性與 IDE 支援
2. **程式碼結構清晰** - 功能劃分明確，邏輯流程易於理解
3. **使用 wait_for_load_state** - 確保頁面載入完成後再擷取資料

---

## 需改進之處

### 🔴 嚴重問題

#### 1. 缺少錯誤處理機制
```python
# 問題：若頁面載入失敗或元素找不到，程式會直接崩潰
page.goto("https://zh.wikipedia.org")
page.locator("#searchInput").fill("臺灣")
```

**建議修正：**
```python
from playwright.sync_api import TimeoutError as PlaywrightTimeout

try:
    page.goto("https://zh.wikipedia.org", timeout=30000)
    page.locator("#searchInput").fill("臺灣", timeout=10000)
except PlaywrightTimeout as e:
    print(f"頁面載入超時: {e}")
    browser.close()
    return
except Exception as e:
    print(f"發生錯誤: {e}")
    browser.close()
    return
```

#### 2. 資源未正確釋放（Context Manager 模式）
```python
# 問題：browser.close() 可能因異常而未被執行
browser = p.chromium.launch()
# ... 操作 ...
browser.close()
```

**建議修正：**
```python
with p.chromium.launch() as browser:
    with browser.new_page() as page:
        # 所有操作都在這裡
        pass
    # 自動關閉分頁與瀏覽器
```

---

### 🟡 中度問題

#### 3. 截圖檔名固定，易被覆蓋
```python
# 問題：每次執行都會覆蓋之前的截圖
page.screenshot(path="screenshot.png")
```

**建議修正：**
```python
import datetime

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
page.screenshot(path=f"screenshot_{timestamp}.png")
```

#### 4. 缺少等待策略
```python
# 問題：直接按 Enter 可能搜尋框尚未完全載入
page.keyboard.press("Enter")
```

**建議修正：**
```python
page.locator("#searchInput").wait_for(state="visible")
page.keyboard.press("Enter")
```

#### 5. 字串截斷可能導致亂碼
```python
# 問題：中文字符截斷可能導致編碼問題
print(f"摘要: {content[:100]}")
```

**建議修正：**
```python
# 使用 encode/decode 確保正確截斷
summary = content[:100] + "..." if len(content) > 100 else content
print(f"摘要: {summary}")
```

---

### 🟢 輕微問題

#### 6. 硬編碼的搜尋關鍵字
```python
# 問題：關鍵字寫死，無法重複使用
page.locator("#searchInput").fill("臺灣")
```

**建議修正：**
```python
def crawl(p: Playwright, keyword: str = "臺灣") -> None:
    # ...
    page.locator("#searchInput").fill(keyword)
```

#### 7. 缺少 Headless 模式選項
```python
# 問題：無法切換有頭/無頭模式進行除錯
browser = p.chromium.launch()
```

**建議修正：**
```python
browser = p.chromium.launch(headless=True)  # 或 False 用於除錯
```

#### 8. 印出文字有錯別字
```python
# 第 19 行：「返品首頁」應為「返回首頁」
print(f"返品首頁:{page.title()}")
```

---

## 建議的重構版本

```python
"""
維基百科爬蟲練習 - 改良版
"""

from playwright.sync_api import sync_playwright, Playwright, Browser, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeout
import datetime
import sys


def crawl(p: Playwright, keyword: str = "臺灣", headless: bool = True) -> None:
    """
    維基百科爬蟲函式
    
    Args:
        p: Playwright 實例
        keyword: 搜尋關鍵字
        headless: 是否使用無頭模式
    """
    browser: Browser = None
    
    try:
        # 啟動瀏覽器
        browser = p.chromium.launch(headless=headless)
        page: Page = browser.new_page()
        
        # 設定全域逾時
        page.set_default_timeout(30000)
        
        # 前往維基百科
        print(f"正在前往維基百科...")
        page.goto("https://zh.wikipedia.org")
        
        # 等待搜尋框出現並輸入關鍵字
        search_input = page.locator("#searchInput")
        search_input.wait_for(state="visible")
        search_input.fill(keyword)
        
        # 截圖
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshot_{timestamp}.png"
        page.screenshot(path=screenshot_path)
        print(f"截圖已儲存: {screenshot_path}")
        
        # 執行搜尋
        page.keyboard.press("Enter")
        page.wait_for_load_state("networkidle")
        
        # 擷取搜尋結果
        first_heading: str = page.locator("#firstHeading").inner_text()
        print(f"搜尋主題: {first_heading}")
        
        # 擷取摘要
        content: str = page.locator("#mw-content-text p").first.inner_text()
        summary = content[:100] + "..." if len(content) > 100 else content
        print(f"摘要: {summary}")
        
        # 返回首頁
        page.go_back()
        page.wait_for_load_state("networkidle")
        print(f"返回首頁: {page.title()}")
        
    except PlaywrightTimeout as e:
        print(f"操作逾時: {e}", file=sys.stderr)
    except Exception as e:
        print(f"發生錯誤: {e}", file=sys.stderr)
    finally:
        # 確保瀏覽器被關閉
        if browser:
            browser.close()


if __name__ == "__main__":
    # 支援命令列參數
    keyword = sys.argv[1] if len(sys.argv) > 1 else "臺灣"
    
    with sync_playwright() as p:
        crawl(p, keyword=keyword, headless=True)
```

---

## 總結

| 類別 | 數量 |
|------|------|
| 🔴 嚴重問題 | 2 |
| 🟡 中度問題 | 3 |
| 🟢 輕微問題 | 3 |

### 優先修正建議

1. **立即修正**：加入錯誤處理與資源釋放機制
2. **短期改善**：加入逾時設定與等待策略
3. **長期優化**：改為可重複使用的函式設計

---

## 參考資源

- [Playwright Python 官方文件](https://playwright.dev/python/)
- [Playwright 最佳實踐](https://playwright.dev/python/best-practices)
