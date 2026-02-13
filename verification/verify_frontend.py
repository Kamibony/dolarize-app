from playwright.sync_api import sync_playwright

def verify_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Navigating to http://localhost:5173/")
        page.goto("http://localhost:5173/")

        # Verify Header
        print("Verifying Header...")
        page.wait_for_selector("text=André Digital")
        page.wait_for_selector("text=Extensão Dólarize 2.0")

        # Verify Input Area
        print("Verifying Input Area...")
        input_selector = "input[placeholder='Digite sua mensagem aqui...']"
        page.wait_for_selector(input_selector)

        # Focus and type
        page.focus(input_selector)
        page.type(input_selector, "Quero organizar minhas finanças.", delay=100)

        # Force update?
        page.dispatch_event(input_selector, 'input')

        # Take a screenshot to check if input is filled
        page.screenshot(path="verification/debug_input.png")

        # Wait a bit for svelte reactivity
        page.wait_for_timeout(500)

        # Send Message
        print("Sending Message...")
        # Check if button is enabled
        button = page.locator("text=Enviar")

        if button.is_disabled():
            print("Button is still disabled! Taking screenshot.")
            page.screenshot(path="verification/debug_disabled.png")
        else:
            print("Button is enabled. Clicking...")
            button.click()

            # Verify User Message appears
            print("Verifying User Message...")
            try:
                page.wait_for_selector("text=Quero organizar minhas finanças.", timeout=5000)
                print("User message found.")
            except:
                print("User message NOT found.")

            # Wait for agent response simulation
            page.wait_for_timeout(1500)

        # Take Final Screenshot
        screenshot_path = "verification/frontend_verification.png"
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")

        browser.close()

if __name__ == "__main__":
    verify_frontend()
