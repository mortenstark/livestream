import os
import json
import asyncio
import time
import threading
from config import TTS_FILE_PATH, MAX_LISTEN_ATTEMPTS, LISTEN_TIMEOUT_SECONDS, NOTEBOOK_URL, PODCAST_NAME, RECORDING_DIR
from audio import play_audio_file
from audio_capture import record_audio_from_output
from voicemeeter import VoicemeeterRemote

async def wait_for_listen_mode(page, timeout=30):
    """Venter på at podcasten går i lyttemode (animation vises)"""
    try:
        print("Venter på at podcasten går i lyttemode...")
        # Vent på at animationen bliver SYNLIG
        await page.wait_for_selector('.user-speaking-animation',
                                    state='visible',
                                    timeout=timeout*1000)
        print("🎤 Podcasten er i lyttemode!")
        return True
    except Exception as e:
        print(f"❌ Timeout: Podcasten gik ikke i lyttemode inden for {timeout} sekunder: {e}")
        return False

async def wait_for_answer_mode(page, timeout=30):
    """Venter på at podcasten går i svarmode (animation skjules)"""
    try:
        print("Venter på at podcasten begynder at svare...")
        # Vent på at animationen bliver SKJULT
        await page.wait_for_selector('.user-speaking-animation',
                                    state='hidden',
                                    timeout=timeout*1000)
        print("🤖 Podcasten er i svarmode!")
        return True
    except Exception as e:
        print(f"❌ Timeout: Podcasten gik ikke i svarmode inden for {timeout} sekunder: {e}")
        return False

async def interactive_flow(page, tts_file, record_duration=60, vm=None):
    """Håndterer det komplette flow med afspilning og optagelse, synkroniseret med podcast-tilstand"""
    # 1. Vent på lyttemode
    if not await wait_for_listen_mode(page):
        print("Kunne ikke fortsætte, da podcasten ikke gik i lyttemode")
        return None

    # 2. Afspil TTS-lydfil (spørgsmål)
    print("🔊 Afspiller TTS...")
    play_audio_file(tts_file)
    
    # 3. Vent på at podcasten går i svarmode (dvs. har modtaget input)
    if not await wait_for_answer_mode(page):
        print("Kunne ikke fortsætte, da podcasten ikke gik i svarmode")
        return None

    # 4. Slå A2 til på strip 0 for at kunne optage
    if vm:
        print("Slår A2 til på strip 0 for at kunne optage...")
        vm.set_parameter_float("Strip[0].A2", 1.0)
    
    # 5. Start optagelse af hostens svar
    print("🎙️ Starter optagelse af svar...")
    output_file = record_audio_from_output(
        output_device_name="CABLE Output (VB-Audio Virtual Cable)",
        duration=record_duration,
        output_dir=RECORDING_DIR
    )
    
    # 6. Slå A2 fra igen for at undgå feedback ved næste runde
    if vm:
        print("Slår A2 fra på strip 0 igen...")
        vm.set_parameter_float("Strip[0].A2", 0.0)
    
    print(f"✅ Optagelse gemt som: {output_file}")
    return output_file

async def launch_browser_with_auth():
    """Launch browser with authentication and navigate to NotebookLM"""
    from playwright.async_api import async_playwright

    # Initialiser Voicemeeter for at konfigurere A2 output
    vm = VoicemeeterRemote()
    vm.login()
    
    # Slå A2 fra på strip 0 for at undgå feedback
    print("Slår A2 fra på strip 0 for at undgå feedback...")
    vm.set_parameter_float("Strip[0].A2", 0.0)

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

            # Kør det synkroniserede flow for afspilning og optagelse
            recording_file = await interactive_flow(page, TTS_FILE_PATH, record_duration=60, vm=vm)
            
            if recording_file:
                print(f"Interaktion gennemført! Optagelse gemt som: {recording_file}")
            else:
                print("Interaktionen kunne ikke gennemføres korrekt.")

            # Keep the browser open
            print("\n*** Browser forbliver åben. Tryk Ctrl+C i terminalen for at afslutte programmet. ***")
            print("Du kan køre flere interaktioner ved at trykke Enter...")
            
            # Tillad flere interaktioner
            while True:
                # Vent på brugerinput for at starte en ny interaktion
                await asyncio.get_event_loop().run_in_executor(None, input, "Tryk Enter for at starte en ny interaktion eller Ctrl+C for at afslutte: ")
                
                # Kør en ny interaktion
                recording_file = await interactive_flow(page, TTS_FILE_PATH, record_duration=60, vm=vm)
                
                if recording_file:
                    print(f"Interaktion gennemført! Optagelse gemt som: {recording_file}")
                else:
                    print("Interaktionen kunne ikke gennemføres korrekt.")

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
        finally:
            # Logout from Voicemeeter
            vm.logout()