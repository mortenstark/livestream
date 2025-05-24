# config.py

# Audio device configuration
TTS_OUTPUT_DEVICE = "CABLE Input"  # VB-Cable input device (sender lyd TIL NotebookML)
AUDIO_INPUT_DEVICE = "CABLE Output"  # VB-Cable output device (modtager lyd FRA NotebookML)
AUDIO_DEVICE_INDEX = None  # Lad scriptet finde den korrekte device

# Gain settings
DEFAULT_GAIN = 3.0  # Default gain for audio playback

# TTS file path
TTS_FILE_PATH = "graham.wav"  # Standard TTS fil
TTS_FILE = "graham.wav"  # Alias for backward compatibility

# NotebookLM settings
NOTEBOOK_URL = "https://notebooklm.google.com/"
PODCAST_NAME = "Dr. Farsight Podcast"

# Recording settings
RECORDING_DIR = "recordings"
RECORDING_DURATION = 60  # antal sekunder der optages fra NotebookLM

# Listen settings
MAX_LISTEN_ATTEMPTS = 3
LISTEN_TIMEOUT_SECONDS = 30