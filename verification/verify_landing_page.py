from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # 1. Navigate to the landing page
    print("Navigating to http://localhost:5173/")
    page.goto("http://localhost:5173/")

    # Wait for the landing page content
    try:
        page.wait_for_selector("text=Proteja seu patrimônio", timeout=10000)
    except Exception as e:
        print(f"Error waiting for landing page: {e}")
        page.screenshot(path="verification/error_landing.png")
        browser.close()
        return

    # 2. Screenshot Landing Page
    print("Taking screenshot of Landing Page...")
    page.screenshot(path="verification/landing_page.png")

    # 3. Click the CTA button
    print("Clicking 'Iniciar Diagnóstico'...")
    page.click("text=Iniciar Diagnóstico")

    # 4. Wait for Chat Interface
    print("Waiting for Chat Interface...")
    try:
        page.wait_for_selector("text=André Digital", timeout=10000)
    except Exception as e:
        print(f"Error waiting for chat interface: {e}")
        page.screenshot(path="verification/error_chat.png")
        browser.close()
        return

    # Wait a bit for transition
    page.wait_for_timeout(1000)

    # 5. Screenshot Chat View
    print("Taking screenshot of Chat View...")
    page.screenshot(path="verification/chat_view.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
