from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto("http://localhost:5173/guia")
            page.wait_for_selector("h1:has-text('Manual de Uso: Dólarize 2.0')")
            # Scroll down to capture more content
            page.screenshot(path="verification/guia_page.png", full_page=True)
            print("Screenshot taken successfully.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
