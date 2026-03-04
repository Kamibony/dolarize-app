from playwright.sync_api import sync_playwright

def test_qa_dashboard():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:5173/admin/qa-dashboard")

        # Wait for the dashboard to load (wait for the title to appear)
        page.wait_for_selector("text=QA Dashboard")

        # Take a screenshot
        page.screenshot(path="qa-dashboard.png", full_page=True)
        browser.close()

if __name__ == "__main__":
    test_qa_dashboard()
    print("Screenshot saved to qa-dashboard.png")
