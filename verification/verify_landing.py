from playwright.sync_api import sync_playwright
import sys

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    print("Navigating to http://localhost:5173/ ...")
    try:
        page.goto("http://localhost:5173/", timeout=60000)

        # Check for Headline
        h1 = page.locator('h1')
        h1_text = h1.inner_text()
        print(f"Found H1: {h1_text}")
        if "Construa sua Fortaleza Financeira" not in h1_text:
            print("ERROR: Headline text mismatch!")
            sys.exit(1)

        # Check for Image
        img = page.locator('img[src="/Perfil Oficial Andre Digital.png"]')
        if img.count() == 0:
            # Try encoded just in case
            img = page.locator('img[src="/Perfil%20Oficial%20Andre%20Digital.png"]')

        if img.count() > 0:
            print("Found Image: Perfil Oficial Andre Digital.png")
            # Verify visibility
            if not img.is_visible():
                print("WARNING: Image is not visible!")
        else:
            print("ERROR: Image not found!")
            sys.exit(1)

        # Check for Grid Layout
        # We look for a div with grid-cols-1 and lg:grid-cols-2
        grid = page.locator('.grid.grid-cols-1.lg\\:grid-cols-2')
        if grid.count() > 0:
            print("Found Grid Layout container.")
        else:
            print("ERROR: Grid Layout container not found!")
            sys.exit(1)

        page.screenshot(path="verification/landing_page.png", full_page=True)
        print("Screenshot saved to verification/landing_page.png")

    except Exception as e:
        print(f"Error during verification: {e}")
        sys.exit(1)
    finally:
        browser.close()

with sync_playwright() as playwright:
    run(playwright)
