from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Verify /guia
    print("Navigating to /guia...")
    try:
        page.goto("http://localhost:5173/guia", timeout=30000)
        page.wait_for_selector('h1', timeout=10000)
        print("Page /guia loaded.")
        page.screenshot(path="verification/guia.png", full_page=True)
        print("Screenshot of /guia saved.")
    except Exception as e:
        print(f"Error loading /guia: {e}")

    # Verify /apresentacao
    print("Navigating to /apresentacao...")
    try:
        page.goto("http://localhost:5173/apresentacao", timeout=30000)
        page.wait_for_selector('h1', timeout=10000)
        print("Page /apresentacao loaded.")
        page.screenshot(path="verification/apresentacao.png", full_page=True)
        print("Screenshot of /apresentacao saved.")
    except Exception as e:
        print(f"Error loading /apresentacao: {e}")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
