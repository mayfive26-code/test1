"""對 practice5.py 核心函式的單元測試。"""

from __future__ import annotations

from pathlib import Path

import pytest

from practice5 import URL, WebsiteCheckResult


# ── WebsiteCheckResult ───────────────────────────────────────
class TestWebsiteCheckResult:
    def test_default_values(self):
        """確認資料類別有合理的預設值。"""
        r = WebsiteCheckResult(url="https://example.com/", browser="chromium",
                               headless=True, timeout=30000)
        assert r.url == "https://example.com/"
        assert r.browser == "chromium"
        assert r.headless is True
        assert r.timeout == 30000
        assert r.status is None
        assert r.response_time_ms == 0.0
        assert r.page_title == ""
        assert r.main_heading == ""
        assert r.final_url == ""
        assert r.screenshot_path is None
        assert r.error == ""

    def test_with_values(self):
        """確認可儲存所有欄位值。"""
        r = WebsiteCheckResult(
            url="https://test.com/",
            browser="firefox",
            headless=False,
            timeout=15000,
            status=200,
            response_time_ms=123.4,
            page_title="Test",
            main_heading="Hello",
            final_url="https://test.com/",
            screenshot_path=Path("/tmp/shot.png"),
            error="",
        )
        assert r.status == 200
        assert r.response_time_ms == 123.4
        assert r.page_title == "Test"

    def test_error_state(self):
        """確認可表示錯誤狀態。"""
        r = WebsiteCheckResult(url=URL, browser="chromium",
                               headless=True, timeout=30000,
                               error="連線失敗")
        assert r.error == "連線失敗"


# ── 輔助函式：URL 驗證（從 gui.py 抽取）─────────────────────
# 為避免 gui.py 的 tkinter 匯入干擾測試，直接在測試中定義驗證邏輯。

def is_valid_url(url: str) -> str | None:
    from urllib.parse import urlparse
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
    try:
        t = int(value)
        if t < 1000:
            return False, "超時時間至少為 1000 毫秒（1 秒）"
        if t > 120000:
            return False, "超時時間不可超過 120000 毫秒（120 秒）"
        return True, str(t)
    except ValueError:
        return False, "超時時間必須為整數（毫秒）"


class TestIsValidUrl:
    def test_empty(self):
        assert is_valid_url("") is not None

    def test_no_scheme(self):
        assert is_valid_url("example.com") is not None

    def test_valid_http(self):
        assert is_valid_url("http://example.com/") is None

    def test_valid_https(self):
        assert is_valid_url("https://example.com/") is None

    def test_missing_host(self):
        assert is_valid_url("https://") is not None

    def test_whitespace(self):
        assert is_valid_url("  https://example.com/  ") is None


class TestIsValidTimeout:
    def test_not_integer(self):
        ok, _ = is_valid_timeout("abc")
        assert ok is False

    def test_too_small(self):
        ok, _ = is_valid_timeout("100")
        assert ok is False

    def test_too_large(self):
        ok, _ = is_valid_timeout("200000")
        assert ok is False

    def test_valid(self):
        ok, val = is_valid_timeout("5000")
        assert ok is True
        assert val == "5000"

    def test_boundary_low(self):
        ok, val = is_valid_timeout("1000")
        assert ok is True

    def test_boundary_high(self):
        ok, val = is_valid_timeout("120000")
        assert ok is True
