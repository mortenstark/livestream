import ctypes
import os
import time
from config import VOICEMEETER_DLL_PATH

class VoicemeeterRemote:
    def __init__(self, dll_path=VOICEMEETER_DLL_PATH):
        self.dll_path = dll_path
        self.dll = None
        self.initialized = False

    def load_dll(self):
        """Load the Voicemeeter Remote API DLL"""
        try:
            print(f"Loading DLL from: {self.dll_path}")
            dll = ctypes.cdll.LoadLibrary(self.dll_path)

            # Define function prototypes
            dll.VBVMR_Login = dll.VBVMR_Login
            dll.VBVMR_Login.restype = ctypes.c_long

            dll.VBVMR_Logout = dll.VBVMR_Logout
            dll.VBVMR_Logout.restype = ctypes.c_long

            dll.VBVMR_RunVoicemeeter = dll.VBVMR_RunVoicemeeter
            dll.VBVMR_RunVoicemeeter.argtypes = [ctypes.c_long]
            dll.VBVMR_RunVoicemeeter.restype = ctypes.c_long

            dll.VBVMR_GetVoicemeeterType = dll.VBVMR_GetVoicemeeterType
            dll.VBVMR_GetVoicemeeterType.argtypes = [ctypes.POINTER(ctypes.c_long)]
            dll.VBVMR_GetVoicemeeterType.restype = ctypes.c_long

            dll.VBVMR_GetParameterFloat = dll.VBVMR_GetParameterFloat
            dll.VBVMR_GetParameterFloat.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_float)]
            dll.VBVMR_GetParameterFloat.restype = ctypes.c_long

            dll.VBVMR_GetParameterStringA = dll.VBVMR_GetParameterStringA
            dll.VBVMR_GetParameterStringA.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
            dll.VBVMR_GetParameterStringA.restype = ctypes.c_long

            dll.VBVMR_SetParameterFloat = dll.VBVMR_SetParameterFloat
            dll.VBVMR_SetParameterFloat.argtypes = [ctypes.c_char_p, ctypes.c_float]
            dll.VBVMR_SetParameterFloat.restype = ctypes.c_long

            dll.VBVMR_SetParameterStringA = dll.VBVMR_SetParameterStringA
            dll.VBVMR_SetParameterStringA.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
            dll.VBVMR_SetParameterStringA.restype = ctypes.c_long

            print("DLL functions defined successfully")
            self.dll = dll
            return True
        except Exception as e:
            print(f"Error loading Voicemeeter Remote API: {e}")
            return False

    def login(self):
        """Login to Voicemeeter"""
        if not self.dll:
            if not self.load_dll():
                return False

        # Login to Voicemeeter
        login_result = self.dll.VBVMR_Login()
        print(f"Login successful: {login_result}")

        # Get Voicemeeter type
        vm_type = ctypes.c_long()
        self.dll.VBVMR_GetVoicemeeterType(ctypes.byref(vm_type))

        vm_types = {
            1: "Voicemeeter Standard",
            2: "Voicemeeter Banana",
            3: "Voicemeeter Potato"
        }

        print(f"Connected to {vm_types.get(vm_type.value, 'Unknown Voicemeeter type')}")
        self.initialized = True
        return True

    def logout(self):
        """Logout from Voicemeeter"""
        if self.dll and self.initialized:
            self.dll.VBVMR_Logout()
            print("Logged out from Voicemeeter Remote API")
            self.initialized = False

    def get_parameter_float(self, parameter, debug=False):
        """Get a float parameter from Voicemeeter"""
        if not self.initialized:
            return None
        value = ctypes.c_float()
        result = self.dll.VBVMR_GetParameterFloat(parameter.encode(), ctypes.byref(value))
        if result == 0:
            return value.value
        if debug:
            print(f"Failed to get parameter {parameter}")
        return None

    def set_parameter_float(self, parameter, value):
        """Set a float parameter in Voicemeeter"""
        if not self.initialized:
            return False

        result = self.dll.VBVMR_SetParameterFloat(parameter.encode(), ctypes.c_float(value))
        return result == 0

    def get_parameter_string(self, parameter):
        """Get a string parameter from Voicemeeter"""
        if not self.initialized:
            return None

        value = ctypes.create_string_buffer(512)
        result = self.dll.VBVMR_GetParameterStringA(parameter.encode(), value)
        if result == 0:
            return value.value.decode('utf-8')
        return None

    def set_parameter_string(self, parameter, value):
        """Set a string parameter in Voicemeeter"""
        if not self.initialized:
            return False

        result = self.dll.VBVMR_SetParameterStringA(parameter.encode(), value.encode())
        return result == 0

    def configure_routing(self, debug=False):
        """Configure Voicemeeter for routing TTS audio to NotebookLM"""
        if not self.initialized:
            print("Voicemeeter Remote API not initialized")
            return False

        if debug:
            print("\n--- Current Voicemeeter Configuration ---")
            # Print current configuration
            device = self.get_parameter_string("Strip[0].device.wdm", debug)
            print(f"Strip[0] current device: {device if device else 'Unknown'}")
            for output in ["A1", "A2", "A3", "B1", "B2"]:
                value = self.get_parameter_float(f"Strip[0].{output}", debug)
                print(f"Strip[0].{output} = {value if value is not None else 'Unknown'}")
            device = self.get_parameter_string("Bus[3].device.wdm", debug)
            print(f"Bus[3] current device: {device if device else 'Unknown'}")

        # Configure routing
        print("\n--- Configuring Voicemeeter Routing ---")
        self.set_parameter_string("Strip[0].device.wdm", "CABLE Output (VB-Audio Virtual Cable)")
        self.set_parameter_float("Strip[0].A1", 1.0)
        self.set_parameter_float("Strip[0].A2", 0.0)
        self.set_parameter_float("Strip[0].A3", 0.0)
        self.set_parameter_float("Strip[0].B1", 1.0)
        self.set_parameter_float("Strip[0].B2", 0.0)
        self.set_parameter_string("Bus[3].device.wdm", "CABLE Input (VB-Audio Virtual Cable)")
        self.set_parameter_float("Strip[0].Gain", 0.0)
        self.set_parameter_float("Bus[3].Gain", 0.0)

        if debug:
            print("\n--- Verifying Voicemeeter Configuration ---")
            # Verify configuration
            device = self.get_parameter_string("Strip[0].device.wdm", debug)
            print(f"Strip[0] device now: {device if device else 'Unknown'}")
            for output in ["A1", "A2", "A3", "B1", "B2"]:
                value = self.get_parameter_float(f"Strip[0].{output}", debug)
                print(f"Strip[0].{output} = {value if value is not None else 'Unknown'}")
            device = self.get_parameter_string("Bus[3].device.wdm", debug)
            print(f"Bus[3] device now: {device if device else 'Unknown'}")

        print("Voicemeeter routing configured")
        return True