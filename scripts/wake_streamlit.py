"""Streamlit Community Cloud 앱 자동 깨우기

GitHub Actions가 몇 시간마다 실행한다. 앱 주소를 브라우저로 열어서
- 잠들어 있으면 'Yes, get this app back up!' 버튼을 눌러 깨우고
- 깨어 있으면 방문만 해서 잠드는 시간을 미룬다.
주소는 환경 변수 STREAMLIT_URLS 에 쉼표로 구분해 넣는다.
"""
import os
import sys

from playwright.sync_api import sync_playwright

URLS = [u.strip() for u in os.environ.get("STREAMLIT_URLS", "").split(",") if u.strip()]
WAKE_TEXT = "Yes, get this app back up"


def wake(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(8_000)
    button = page.get_by_role("button", name=WAKE_TEXT)
    if button.count() > 0:
        print(f"[잠들어 있음] {url} -> 깨우는 중")
        button.first.click()
        page.wait_for_timeout(90_000)  # 앱이 다시 켜질 때까지 기다림
        still = page.get_by_role("button", name=WAKE_TEXT).count() > 0
        print(f"[{'아직 잠듦' if still else '깨움'}] {url}")
        return not still
    print(f"[깨어 있음] {url}")
    return True


def main():
    if not URLS:
        print("STREAMLIT_URLS 가 비어 있어요")
        sys.exit(1)
    ok = True
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for url in URLS:
            page = browser.new_page()
            try:
                ok = wake(page, url) and ok
            except Exception as e:  # 한 앱이 실패해도 나머지는 계속
                print(f"[실패] {url}: {e}")
                ok = False
            finally:
                page.close()
        browser.close()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
