from playwright.sync_api import sync_playwright
import time

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    page.on("console", lambda msg: print(f"Browser Console: {msg.text}"))
    page.on("pageerror", lambda err: print(f"Browser Error: {err}"))

    print("Navigating to http://localhost:5173/admin/qa-dashboard ...")
    try:
        page.goto("http://localhost:5173/admin/qa-dashboard", timeout=60000)

        # Give it time to load data from Firebase (or fail)
        page.wait_for_timeout(5000)

        # Let's inspect the entire HTML
        print(page.content())

    except Exception as e:
        print(f"Error during verification: {e}")
    finally:
        browser.close()

with sync_playwright() as playwright:
    run(playwright)
