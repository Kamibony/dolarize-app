from playwright.sync_api import sync_playwright, expect
import os

def test_crm_columns(page):
    # Mock the API responses
    page.route("**/admin/users", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='''[
            {
                "id": "user123",
                "nome": "João Silva",
                "email": "joao@example.com",
                "classificacao_lead": "A - Quente",
                "dor_principal": "Medo de inflação",
                "maturidade": "iniciante",
                "tags": ["vip"]
            },
            {
                "id": "user456",
                "nome": null,
                "email": null,
                "classificacao_lead": "C - Frio",
                "dor_principal": null,
                "maturidade": null,
                "tags": []
            }
        ]'''
    ))

    page.route("**/admin/stats", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='''{
            "total_leads": 2,
            "conversion_rate_a": 50.0,
            "funnel_distribution": {"A": 1, "B": 0, "C": 1}
        }'''
    ))

    # Navigate to the admin page
    # Since we are running locally, we need to know the port.
    # I'll assume 4173 for preview or 5173 for dev.
    page.goto("http://localhost:4173/admin")

    # Wait for the table to load
    page.wait_for_selector("table")

    # Verify headers
    headers = page.locator("thead th")
    expect(headers.nth(0)).to_have_text("ID")
    expect(headers.nth(1)).to_have_text("Nome")
    expect(headers.nth(2)).to_have_text("E-mail")

    # Verify data row 1
    row1 = page.locator("tbody tr").nth(0)
    expect(row1.locator("td").nth(1)).to_have_text("João Silva")
    expect(row1.locator("td").nth(2)).to_have_text("joao@example.com")

    # Verify data row 2 (placeholders)
    row2 = page.locator("tbody tr").nth(1)
    expect(row2.locator("td").nth(1)).to_have_text("Aguardando...")
    expect(row2.locator("td").nth(2)).to_have_text("Aguardando...")

    # Take screenshot
    if not os.path.exists("verification"):
        os.makedirs("verification")
    page.screenshot(path="verification/crm_columns.png")
    print("Screenshot saved to verification/crm_columns.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            test_crm_columns(page)
        except Exception as e:
            print(f"Test failed: {e}")
            page.screenshot(path="verification/error.png")
        finally:
            browser.close()
