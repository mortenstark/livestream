import os
import time
import subprocess
import ctypes
from pathlib import Path
import json

# Constants
VOICEMEETER_TYPE = 2  # 2 = Banana
STRIP_INDEX = 0  # First hardware strip (zero-based)
BUS_INDEX = 3  # B1 (zero-based: A1=0, A2=1, A3=2, B1=3, B2=4)
TTS_FILE = "graham.wav"
NOTEBOOKLM_URL = "https://notebooklm.google.com/"

class VoicemeeterRemote:
    def __init__(self):
        self.dll = None
        self.vm_path = None
        self.is_connected = False
        self.init_dll()

    def init_dll(self):
        """Initialize the Voicemeeter Remote DLL"""
        # Find Voicemeeter installation path from registry
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\VB:Voicemeeter {17359A74-1236-5467}") as key:
                self.vm_path = winreg.QueryValueEx(key, "UninstallString")[0].replace("uninstall.exe", "")
        except Exception as e:
            print(f"Error finding Voicemeeter in registry: {e}")
            # Fallback to common installation path
            self.vm_path = r"C:\Program Files\VB\Voicemeeter"

        # Load the appropriate DLL
        dll_path = os.path.join(self.vm_path, "VoicemeeterRemote64.dll" if ctypes.sizeof(ctypes.c_void_p) == 8 else "VoicemeeterRemote.dll")
        print(f"Loading DLL from: {dll_path}")

        try:
            self.dll = ctypes.cdll.LoadLibrary(dll_path)

            # Define function prototypes
            self.dll.VBVMR_Login.restype = ctypes.c_long
            self.dll.VBVMR_Logout.restype = ctypes.c_long
            self.dll.VBVMR_RunVoicemeeter.argtypes = [ctypes.c_long]
            self.dll.VBVMR_RunVoicemeeter.restype = ctypes.c_long
            self.dll.VBVMR_IsParametersDirty.restype = ctypes.c_long
            self.dll.VBVMR_GetVoicemeeterType.argtypes = [ctypes.POINTER(ctypes.c_long)]
            self.dll.VBVMR_GetVoicemeeterType.restype = ctypes.c_long
            self.dll.VBVMR_SetParameterFloat.argtypes = [ctypes.c_char_p, ctypes.c_float]
            self.dll.VBVMR_SetParameterFloat.restype = ctypes.c_long
            self.dll.VBVMR_SetParameterStringA.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
            self.dll.VBVMR_SetParameterStringA.restype = ctypes.c_long

            print("DLL functions defined successfully")
        except Exception as e:
            print(f"Error loading DLL: {e}")
            self.dll = None

    def login(self):
        """Login to Voicemeeter Remote API"""
        if not self.dll:
            print("DLL not loaded")
            return False

        result = self.dll.VBVMR_Login()
        if result < 0:
            print(f"Failed to login: {result}")
            return False

        print(f"Login successful: {result}")
        self.is_connected = True

        # If Voicemeeter is not running, start it
        if result == 1:
            print(f"Starting Voicemeeter Banana...")
            self.dll.VBVMR_RunVoicemeeter(VOICEMEETER_TYPE)
            time.sleep(2)  # Wait for Voicemeeter to initialize

        # Initialize parameters
        self.dll.VBVMR_IsParametersDirty()
        return True

    def logout(self):
        """Logout from Voicemeeter Remote API"""
        if self.dll and self.is_connected:
            self.dll.VBVMR_Logout()
            self.is_connected = False
            print("Logged out from Voicemeeter Remote API")

    def set_parameter_float(self, param_name, value):
        """Set a float parameter in Voicemeeter"""
        if not self.is_connected:
            print("Not connected to Voicemeeter")
            return False

        result = self.dll.VBVMR_SetParameterFloat(param_name.encode(), ctypes.c_float(value))
        if result < 0:
            print(f"Failed to set parameter {param_name}: {result}")
            return False
        return True

    def set_parameter_string(self, param_name, value):
        """Set a string parameter in Voicemeeter"""
        if not self.is_connected:
            print("Not connected to Voicemeeter")
            return False

        result = self.dll.VBVMR_SetParameterStringA(param_name.encode(), value.encode())
        if result < 0:
            print(f"Failed to set parameter {param_name}: {result}")
            return False
        return True

    def configure_routing(self):
        """Configure Voicemeeter routing for NotebookLM TTS capture"""
        # Set Strip[0] to use CABLE Input
        self.set_parameter_string(f"Strip[{STRIP_INDEX}].device.wdm", "CABLE Input (VB-Audio Virtual Cable)")

        # Reset all bus assignments for Strip[0]
        for bus in ["A1", "A2", "A3", "B1", "B2"]:
            self.set_parameter_float(f"Strip[{STRIP_INDEX}].{bus}", 0)

        # Assign Strip[0] to Bus B1
        self.set_parameter_float(f"Strip[{STRIP_INDEX}].B1", 1)

        # Set Bus B1 to use CABLE Output
        self.set_parameter_string(f"Bus[{BUS_INDEX}].device.wdm", "CABLE Output (VB-Audio Virtual Cable)")

        # Set gain levels
        self.set_parameter_float(f"Strip[{STRIP_INDEX}].Gain", 0.0)  # 0dB gain on Strip[0]
        self.set_parameter_float(f"Bus[{BUS_INDEX}].Gain", 0.0)      # 0dB gain on Bus B1

        print("Voicemeeter routing configured")

def play_audio_file(file_path):
    """Play an audio file using Python"""
    try:
        import sounddevice as sd
        import soundfile as sf

        # Load the audio file
        data, samplerate = sf.read(file_path)

        # Get the list of audio devices
        devices = sd.query_devices()

        # Find the CABLE Input device
        cable_device = None
        for i, device in enumerate(devices):
            if "CABLE Input" in device['name'] and device['max_output_channels'] > 0:
                cable_device = i
                break

        if cable_device is None:
            print("CABLE Input device not found")
            # Try to find any Voicemeeter input as fallback
            for i, device in enumerate(devices):
                if "VoiceMeeter" in device['name'] and device['max_output_channels'] > 0:
                    cable_device = i
                    print(f"Using fallback device: {device['name']}")
                    break
            if cable_device is None:
                print("No suitable audio output device found")
                return False

        print(f"Playing audio to device {cable_device}: {devices[cable_device]['name']}")

        # Play the audio file
        sd.play(data, samplerate, device=cable_device)
        sd.wait()  # Wait until the audio is finished

        print("Audio playback completed")
        return True
    except Exception as e:
        print(f"Error playing audio: {e}")
        return False

async def launch_browser_with_auth():
    """Launch browser with authentication and navigate to NotebookLM"""
    from playwright.async_api import async_playwright
    import asyncio

    async with async_playwright() as p:
        # Launch browser with microphone permissions
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--use-fake-ui-for-media-stream",
                "--autoplay-policy=no-user-gesture-required",
            ]
        )

        # Create a new context with microphone permissions
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

        # Navigate to NotebookLM
        await page.goto(NOTEBOOKLM_URL)
        print("Browser launched with NotebookLM")

        # Wait for user to set up NotebookLM in Interactive Mode
        print("Please set up NotebookLM in Interactive Mode and press Enter when ready...")
        await asyncio.get_event_loop().run_in_executor(None, input)

        # Play the TTS audio file
        play_audio_file(TTS_FILE)

        # Keep the browser open
        print("Press Enter to close the browser...")
        await asyncio.get_event_loop().run_in_executor(None, input)

        # Close the browser
        await browser.close()

async def main_async():
    # Initialize Voicemeeter Remote API
    vmr = VoicemeeterRemote()

    # Login to Voicemeeter Remote API
    if not vmr.login():
        print("Failed to connect to Voicemeeter")
        return

    try:
        # Configure Voicemeeter routing
        vmr.configure_routing()

        # Launch browser with NotebookLM
        await launch_browser_with_auth()
    finally:
        # Logout from Voicemeeter Remote API
        vmr.logout()

def main():
    import asyncio
    asyncio.run(main_async())

if __name__ == "__main__":
    main()