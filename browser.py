import os
import json
import asyncio
import time
import threading
import traceback
import numpy as np
import sounddevice as sd
import soundfile as sf
from config import TTS_FILE_PATH, MAX_LISTEN_ATTEMPTS, LISTEN_TIMEOUT_SECONDS, NOTEBOOK_URL, PODCAST_NAME, RECORDING_DIR, DEFAULT_GAIN, AUDIO_DEVICE_INDEX, TTS_OUTPUT_DEVICE, AUDIO_INPUT_DEVICE
from audio_capture import record_audio_from_output
from audio import list_audio_devices

async def wait_for_listen_mode(page, timeout=30, debug_mode=False):
    """Venter på at podcasten går i lyttemode (animation vises)"""
    try:
        if debug_mode:
            print("DEBUG: Venter på at podcasten går i lyttemode...")
        await page.wait_for_selector('.user-speaking-animation[style*="display: block"]', timeout=timeout*1000)
        if debug_mode:
            print("DEBUG: 🎤 Podcasten er i lyttemode!")
        return True
    except Exception as e:
        if debug_mode:
            print(f"DEBUG: ❌ Timeout: Podcasten gik ikke i lyttemode inden for {timeout} sekunder: {e}")
        return False

async def wait_for_answer_mode(page, timeout=30, debug_mode=False):
    """Venter på at podcasten går i svarmode (animation skjules)"""
    try:
        if debug_mode:
            print("DEBUG: Venter på at podcasten begynder at svare...")
        await page.wait_for_selector('.user-speaking-animation[style*="display: none"]', timeout=timeout*1000)
        if debug_mode:
            print("DEBUG: 🤖 Podcasten er i svarmode!")
        return True
    except Exception as e:
        if debug_mode:
            print(f"DEBUG: ❌ Timeout: Podcasten gik ikke i svarmode inden for {timeout} sekunder: {e}")
        return False

async def interactive_flow(page, tts_file, record_duration=60, monitor=True, debug_mode=False):
    """Håndterer det komplette flow med afspilning og optagelse, synkroniseret med podcast-tilstand"""
    try:
        if debug_mode:
            print("DEBUG: Starting interactive_flow")

        # 1. Vent på lyttemode
        if debug_mode:
            print("DEBUG: Waiting for listen mode")
        if not await wait_for_listen_mode(page, debug_mode=debug_mode):
            if debug_mode:
                print("DEBUG: Could not continue, podcast did not enter listen mode")
            return None

        # 2. Afspil TTS-lydfil (spørgsmål) direkte med sounddevice
        if debug_mode:
            print("DEBUG: About to play audio file directly")
            print(f"DEBUG: Audio file path: {tts_file}")

        # Find CABLE Input device
        devices = sd.query_devices()
        cable_input_index = None

        for i, device in enumerate(devices):
            if "CABLE Input" in device['name'] and device.get('max_output_channels', 0) > 0:
                cable_input_index = i
                if debug_mode:
                    print(f"DEBUG: Found CABLE Input at device index {i}")
                break

        if cable_input_index is None:
            if debug_mode:
                print("DEBUG: Could not find CABLE Input device")
            return None

        # Afspil direkte til CABLE Input med korrekt sample rate
        device_info = sd.query_devices(cable_input_index)

        if debug_mode:
            print(f"DEBUG: Using device #{cable_input_index}: {device_info['name']}")
            print(f"DEBUG: Max output channels: {device_info['max_output_channels']}")
            print(f"DEBUG: Default sample rate: {device_info['default_samplerate']} Hz")

        # Indlæs lydfilen
        try:
            # Brug samme metode som i test_audio_simple.py
            data, file_samplerate = sf.read(tts_file)
            if debug_mode:
                print(f"DEBUG: Audio file loaded: {tts_file}")
                print(f"DEBUG: Sample rate: {file_samplerate} Hz")
                print(f"DEBUG: Channels: {data.shape[1] if len(data.shape) > 1 else 1}")
                print(f"DEBUG: Duration: {len(data)/file_samplerate:.2f} seconds")

            # Resample til device'ets sample rate hvis nødvendigt
            target_samplerate = int(device_info['default_samplerate'])
            if file_samplerate != target_samplerate:
                if debug_mode:
                    print(f"DEBUG: Resampling from {file_samplerate} Hz to {target_samplerate} Hz")
                try:
                    import scipy.signal
                    # Beregn antal samples i den nye sample rate
                    num_samples = int(len(data) * target_samplerate / file_samplerate)
                    # Resample data
                    if len(data.shape) > 1:  # Hvis stereo eller flere kanaler
                        resampled_data = np.zeros((num_samples, data.shape[1]))
                        for channel in range(data.shape[1]):
                            resampled_data[:, channel] = scipy.signal.resample(data[:, channel], num_samples)
                        data = resampled_data
                    else:  # Hvis mono
                        data = scipy.signal.resample(data, num_samples)
                    if debug_mode:
                        print(f"DEBUG: Resampled to {len(data)} samples")
                except ImportError:
                    if debug_mode:
                        print("DEBUG: scipy not installed, skipping resampling")
                    print("WARNING: Sample rate mismatch may cause issues. Install scipy for resampling.")

            # Anvend gain
            gain = DEFAULT_GAIN
            data = data * gain
            data = np.clip(data, -1.0, 1.0)  # Undgå forvrængning

            # Konverter til stereo hvis nødvendigt (begrænset til max 2 kanaler)
            channels = min(2, device_info.get('max_output_channels', 2))
            if len(data.shape) == 1 and channels > 1:
                data = np.tile(data.reshape(-1, 1), (1, channels))
            elif len(data.shape) > 1 and data.shape[1] > channels:
                data = data[:, :channels]

            if debug_mode:
                print(f"DEBUG: Playing audio with gain {gain}...")
                print(f"DEBUG: Final audio shape: {data.shape}")
                print(f"DEBUG: Using sample rate: {target_samplerate} Hz")

            # Afspil lyden direkte med korrekt sample rate
            sd.play(data, target_samplerate, device=cable_input_index)
            sd.wait()  # Vent til afspilningen er færdig

            if debug_mode:
                print("DEBUG: Audio playback completed")

        except Exception as e:
            if debug_mode:
                print(f"DEBUG: Error playing audio: {e}")
                import traceback
                traceback.print_exc()
            return None

        # Vent lidt efter afspilning
        if debug_mode:
            print("DEBUG: Waiting 2 seconds after audio playback")
        await asyncio.sleep(2)

        # 3. Vent på at podcasten går i svarmode (dvs. har modtaget input)
        if debug_mode:
            print("DEBUG: Waiting for answer mode")
        if not await wait_for_answer_mode(page, debug_mode=debug_mode):
            if debug_mode:
                print("DEBUG: Could not continue, podcast did not enter answer mode")
            return None

        # 4. Start optagelse af hostens svar
        if debug_mode:
            print("DEBUG: Starting recording")
        output_file = record_audio_from_output(
            output_device_name=AUDIO_INPUT_DEVICE,
            duration=record_duration,
            output_dir=RECORDING_DIR,
            monitor=monitor
        )
        if debug_mode:
            print(f"DEBUG: Recording completed, output_file={output_file}")

        if debug_mode:
            print(f"DEBUG: ✅ Optagelse gemt som: {output_file}")
        else:
            print(f"✅ Optagelse gemt som: {output_file}")
        return output_file

    except Exception as e:
        if debug_mode:
            print(f"DEBUG: Error in interactive_flow: {e}")
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
        else:
            print(f"Error during interactive flow: {e}")
        return None

async def launch_browser_with_auth(debug_mode=False):
    """Launch browser with authentication and navigate to NotebookLM"""
    from playwright.async_api import async_playwright

    if debug_mode:
        print("DEBUG: Starting launch_browser_with_auth()")

    # Verify audio devices are available
    if debug_mode:
        print("DEBUG: Checking audio devices...")
    else:
        print("Checking audio devices...")
    devices = list_audio_devices()

    # Check if CABLE Input and Output are available
    cable_input_found = False
    cable_output_found = False

    for i, device in enumerate(devices):
        if TTS_OUTPUT_DEVICE in device['name'] and device.get('max_output_channels', 0) > 0:
            cable_input_found = True
            if debug_mode:
                print(f"DEBUG: Found {TTS_OUTPUT_DEVICE} at device index {i}")
            else:
                print(f"Found {TTS_OUTPUT_DEVICE} at device index {i}")
        if AUDIO_INPUT_DEVICE in device['name'] and device.get('max_input_channels', 0) > 0:
            cable_output_found = True
            if debug_mode:
                print(f"DEBUG: Found {AUDIO_INPUT_DEVICE} at device index {i}")
            else:
                print(f"Found {AUDIO_INPUT_DEVICE} at device index {i}")

    if not cable_input_found or not cable_output_found:
        if debug_mode:
            print("DEBUG: WARNING: Required audio devices not found. Audio routing may not work correctly.")
            print("DEBUG: Please ensure VB-Cable is properly installed and configured.")
        else:
            print("WARNING: Required audio devices not found. Audio routing may not work correctly.")
            print("Please ensure VB-Cable is properly installed and configured.")

    async with async_playwright() as p:
        if debug_mode:
            print("DEBUG: Launching browser with Playwright")

        # Launch Chromium with specific arguments for microphone access
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--use-fake-ui-for-media-stream",  # Automatically accept microphone permissions
                "--autoplay-policy=no-user-gesture-required",
            ]
        )

        if debug_mode:
            print("DEBUG: Browser launched")

        # Create a new context with explicit microphone permissions
        context = await browser.new_context(
            permissions=["microphone"],
        )

        if debug_mode:
            print("DEBUG: Browser context created with microphone permissions")

        # Load cookies from auth.json if it exists
        if os.path.exists("auth.json"):
            try:
                if debug_mode:
                    print("DEBUG: Loading auth.json")
                with open("auth.json", "r") as f:
                    auth_data = json.load(f)

                cookies = auth_data.get("cookies", [])
                if cookies:
                    await context.add_cookies(cookies)
                    if debug_mode:
                        print("DEBUG: Loaded authentication cookies from auth.json")
                    else:
                        print("Loaded authentication cookies from auth.json")
                else:
                    if debug_mode:
                        print("DEBUG: Warning: auth.json contains no cookies")
                    else:
                        print("Warning: auth.json contains no cookies")
            except Exception as e:
                if debug_mode:
                    print(f"DEBUG: Error loading auth.json: {e}")
                else:
                    print(f"Error loading auth.json: {e}")
        else:
            if debug_mode:
                print("DEBUG: Warning: auth.json not found - login will be required")
            else:
                print("Warning: auth.json not found - login will be required")

        # Create a new page
        page = await context.new_page()

        if debug_mode:
            print("DEBUG: Browser page created")

        try:
            # Set microphone permissions directly for the page
            if debug_mode:
                print("DEBUG: Setting microphone permissions for notebooklm.google.com")
            await context.grant_permissions(["microphone"], origin="https://notebooklm.google.com")

            # I browser.py, når vi instruerer brugeren:
            print("\n*** VIGTIGT: Mikrofonindstillinger i Chromium ***")
            print("1. Åbn Chromium's indstillinger manuelt (tre prikker øverst til højre)")
            print("2. Gå til Indstillinger > Webstedstilladelser > Mikrofon")
            print("3. Vælg 'CABLE Output (VB-Audio Virtual Cable)' fra dropdown-menuen")
            print("   Dette gør at NotebookML modtager lyd FRA dit program via VB-Cable")
            print("4. Scriptet fortsætter om 15 sekunder...")
            await asyncio.sleep(3)

            # Navigate to NotebookLM and set up Dr. Farsight Podcast
            if debug_mode:
                print("DEBUG: Navigating to NotebookLM...")
            else:
                print("Navigating to NotebookLM...")
            await page.goto('https://notebooklm.google.com/')

            if debug_mode:
                print("DEBUG: Navigation to NotebookLM completed")

            # Wait a bit to ensure the page is loaded
            await asyncio.sleep(2)

            if debug_mode:
                print("DEBUG: Clicking on Dr. Farsight Podcast...")
            else:
                print("Clicking on Dr. Farsight Podcast...")
            await page.click('text=Dr. Farsight Podcast')

            if debug_mode:
                print("DEBUG: Clicked on Dr. Farsight Podcast")

            # Wait for the podcast page to load
            await asyncio.sleep(3)

            if debug_mode:
                print("DEBUG: Waiting for Interactive mode option...")
            else:
                print("Waiting for Interactive mode option...")
            await page.wait_for_selector('text=Interactive mode', timeout=30000)

            if debug_mode:
                print("DEBUG: Interactive mode option found")

            if debug_mode:
                print("DEBUG: Clicking on Interactive mode...")
            else:
                print("Clicking on Interactive mode...")
            await page.click('text=Interactive mode')

            if debug_mode:
                print("DEBUG: Clicked on Interactive mode")

            # Wait a bit after clicking on Interactive mode
            await asyncio.sleep(2)

            if debug_mode:
                print("DEBUG: Clicking Play audio button...")
            else:
                print("Clicking Play audio button...")
            await page.click('button[aria-label="Play audio"]')

            if debug_mode:
                print("DEBUG: Clicked Play audio button")

            # Wait for the Join button to be enabled
            if debug_mode:
                print("DEBUG: Waiting for Join button to be enabled...")
            else:
                print("Waiting for Join button to be enabled...")
            await page.wait_for_selector('button:has-text("Join"):not([disabled])', timeout=30000)

            if debug_mode:
                print("DEBUG: Join button is enabled")

            if debug_mode:
                print("DEBUG: Clicking Join button...")
            else:
                print("Clicking Join button...")
            await page.click('button:has-text("Join")')

            if debug_mode:
                print("DEBUG: Clicked Join button")
                print("DEBUG: Successfully set up NotebookLM in Interactive Mode")
            else:
                print("Successfully set up NotebookLM in Interactive Mode")

            # Kør det synkroniserede flow for afspilning og optagelse
            if debug_mode:
                print("DEBUG: Starting interactive flow")
            recording_file = await interactive_flow(page, TTS_FILE_PATH, record_duration=60, debug_mode=debug_mode)

            if recording_file:
                if debug_mode:
                    print(f"DEBUG: Interaktion gennemført! Optagelse gemt som: {recording_file}")
                else:
                    print(f"Interaktion gennemført! Optagelse gemt som: {recording_file}")
            else:
                if debug_mode:
                    print("DEBUG: Interaktionen kunne ikke gennemføres korrekt.")
                else:
                    print("Interaktionen kunne ikke gennemføres korrekt.")

            # Keep the browser open
            if debug_mode:
                print("\nDEBUG: *** Browser forbliver åben. Tryk Ctrl+C i terminalen for at afslutte programmet. ***")
                print("DEBUG: Du kan køre flere interaktioner ved at trykke Enter...")
            else:
                print("\n*** Browser forbliver åben. Tryk Ctrl+C i terminalen for at afslutte programmet. ***")
                print("Du kan køre flere interaktioner ved at trykke Enter...")

            # Tillad flere interaktioner
            while True:
                # Vent på brugerinput for at starte en ny interaktion
                if debug_mode:
                    print("DEBUG: Waiting for user input to start a new interaction")
                await asyncio.get_event_loop().run_in_executor(None, input, "Tryk Enter for at starte en ny interaktion eller Ctrl+C for at afslutte: ")

                if debug_mode:
                    print("DEBUG: Starting a new interaction")

                # Kør en ny interaktion
                recording_file = await interactive_flow(page, TTS_FILE_PATH, record_duration=60, debug_mode=debug_mode)

                if recording_file:
                    if debug_mode:
                        print(f"DEBUG: Interaktion gennemført! Optagelse gemt som: {recording_file}")
                    else:
                        print(f"Interaktion gennemført! Optagelse gemt som: {recording_file}")
                else:
                    if debug_mode:
                        print("DEBUG: Interaktionen kunne ikke gennemføres korrekt.")
                    else:
                        print("Interaktionen kunne ikke gennemføres korrekt.")

        except Exception as e:
            if debug_mode:
                print(f"DEBUG: Error during browser navigation: {e}")
                print(f"DEBUG: Traceback: {traceback.format_exc()}")
            else:
                print(f"Error during browser navigation: {e}")

            # Take a screenshot to help diagnose the issue
            try:
                screenshot_path = "error_screenshot.png"
                if debug_mode:
                    print(f"DEBUG: Taking screenshot and saving to {screenshot_path}")
                await page.screenshot(path=screenshot_path)
                if debug_mode:
                    print(f"DEBUG: Screenshot saved as {screenshot_path}")
                else:
                    print(f"Screenshot saved as {screenshot_path}")
            except Exception as screenshot_error:
                if debug_mode:
                    print(f"DEBUG: Error taking screenshot: {screenshot_error}")
                else:
                    print(f"Error taking screenshot: {screenshot_error}")

            # Wait for the user to terminate the program
            if debug_mode:
                print("\nDEBUG: *** En fejl opstod. Browser forbliver åben. Tryk Ctrl+C i terminalen for at afslutte programmet. ***")
            else:
                print("\n*** En fejl opstod. Browser forbliver åben. Tryk Ctrl+C i terminalen for at afslutte programmet. ***")
            while True:
                await asyncio.sleep(1)