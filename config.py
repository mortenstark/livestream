import os

# Eksisterende konfiguration
VOICEMEETER_TYPE = 1  # 1 = Banana (ikke 2 = Potato)
STRIP_INDEX = 0  # First hardware strip (zero-based)
BUS_INDEX = 3  # B1 (zero-based: A1=0, A2=1, A3=2, B1=3, B2=4)
TTS_FILE = "graham.wav"
VOICEMEETER_DLL_PATH = r"A:\Docker\livestream\spike_claude\VoicemeeterRemote64.dll"

# Nye konfigurationsparametre
# Sti til TTS-filen (bruger den eksisterende TTS_FILE)
TTS_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), TTS_FILE)

# Audio konfiguration
AUDIO_SAMPLE_RATE = 44100
AUDIO_CHANNELS = 1

# NotebookLM konfiguration
NOTEBOOK_URL = "https://notebooklm.google.com/"
PODCAST_NAME = "Dr. Farsight Podcast"

# Optagelseskonfiguration
RECORDING_DIR = "recordings"
RECORDING_DURATION = 60  # sekunder

# Lyttedetektering konfiguration
MAX_LISTEN_ATTEMPTS = 3
LISTEN_TIMEOUT_SECONDS = 30