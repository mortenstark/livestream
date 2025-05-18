import os
import json
import asyncio
from config import TTS_FILE
from audio import play_audio_file

async def launch_browser_with_auth():
    """Launch browser with authentication and navigate to NotebookLM"""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        # Launch Chromium with specific arguments for microphone access
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--use-fake-ui-for-media-stream",  # Automatically accept microphone permissions
                "--autoplay-policy=no-user-gesture-required",
            ]
        )

        # Create a new context with explicit microphone permissions
        context = await browser.new_context(
            permissions=["microphone"],
        )

        # Load cookies from auth.json if it exists
        if os.path.exists("auth.json"):
            try:
                with open("auth.json", "r") as f:
                    auth_data = json.load(f)

                cookies = auth_data.get("cookies", [])
                if cookies:
                    await context.add_cookies(cookies)
                    print("Loaded authentication cookies from auth.json")
                else:
                    print("Warning: auth.json contains no cookies")
            except Exception as e:
                print(f"Error loading auth.json: {e}")
        else:
            print("Warning: auth.json not found - login will be required")

        # Create a new page
        page = await context.new_page()

        try:
            # Set microphone permissions directly for the page
            await context.grant_permissions(["microphone"], origin="https://notebooklm.google.com")

            # Manually set the microphone to CABLE Output
            print("\n*** VIGTIGT: Mikrofonindstillinger i Chromium ***")
            print("1. Åbn Chromium's indstillinger manuelt (tre prikker øverst til højre)")
            print("2. Gå til Indstillinger > Webstedstilladelser > Mikrofon")
            print("3. Vælg 'CABLE Output (VB-Audio Virtual Cable)' fra dropdown-menuen")
            print("4. Scriptet fortsætter om 15 sekunder...")
            await asyncio.sleep(1)

            # Navigate to NotebookLM and set up Dr. Farsight Podcast
            print("Navigating to NotebookLM...")
            await page.goto('https://notebooklm.google.com/')

            # Wait a bit to ensure the page is loaded
            await asyncio.sleep(2)

            print("Clicking on Dr. Farsight Podcast...")
            await page.click('text=Dr. Farsight Podcast')

            # Wait for the podcast page to load
            await asyncio.sleep(3)

            print("Waiting for Interactive mode option...")
            await page.wait_for_selector('text=Interactive mode', timeout=30000)

            print("Clicking on Interactive mode...")
            await page.click('text=Interactive mode')

            # Wait a bit after clicking on Interactive mode
            await asyncio.sleep(2)

            print("Clicking Play audio button...")
            await page.click('button[aria-label="Play audio"]')

            # Wait for the Join button to be enabled
            print("Waiting for Join button to be enabled...")
            await page.wait_for_selector('button:has-text("Join"):not([disabled])', timeout=30000)

            print("Clicking Join button...")
            await page.click('button:has-text("Join")')

            print("Successfully set up NotebookLM in Interactive Mode")

            # Wait a moment for the interface to stabilize
            await asyncio.sleep(5)

            # Play the TTS audio file
            print("Playing TTS audio file...")
            play_audio_file()

            # Wait a bit after playing the audio file
            print("Waiting 15 seconds after audio playback...")
            await asyncio.sleep(15)

            # Play the audio file again to ensure it's captured
            print("Playing TTS audio file again...")
            play_audio_file()

            # Keep the browser open
            print("\n*** Browser forbliver åben. Tryk Ctrl+C i terminalen for at afslutte programmet. ***")

            # Wait for the user to terminate the program
            while True:
                await asyncio.sleep(1)

        except Exception as e:
            print(f"Error during browser navigation: {e}")

            # Take a screenshot to help diagnose the issue
            try:
                await page.screenshot(path="error_screenshot.png")
                print("Screenshot saved as error_screenshot.png")
            except Exception as screenshot_error:
                print(f"Error taking screenshot: {screenshot_error}")

            # Wait for the user to terminate the program
            print("\n*** En fejl opstod. Browser forbliver åben. Tryk Ctrl+C i terminalen for at afslutte programmet. ***")
            while True:
                await asyncio.sleep(1)