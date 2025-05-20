from config import TTS_FILE
import sounddevice as sd
import soundfile as sf
import os

def play_audio_file(file_path=TTS_FILE, debug=False):
    """Play an audio file using sounddevice to CABLE-A Input (VB-Audio Virtual Cable A)"""
    try:
        # Find device index for CABLE-A Input
        devices = sd.query_devices()
        cable_a_index = None
        for i, d in enumerate(devices):
            if "CABLE-A Input" in d['name'] and d['max_output_channels'] > 0:
                cable_a_index = i
                break
        if cable_a_index is None:
            print("CABLE-A Input (VB-Audio Virtual Cable A) not found!")
            return False

        if debug:
            print(f"Using device index {cable_a_index}: {devices[cable_a_index]['name']}")

        # Load the audio file
        data, samplerate = sf.read(file_path)
        if debug:
            print(f"Playing {file_path} at {samplerate} Hz")

        # Play the audio file to CABLE-A Input
        print("Starting audio playback to CABLE-A Input...")
        sd.play(data, samplerate, device=cable_a_index)
        sd.wait()
        print("Audio playback completed")
        return True

    except Exception as e:
        print(f"Error playing audio: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    play_audio_file(debug=True)