from config import TTS_FILE, TTS_OUTPUT_DEVICE
import sounddevice as sd
import soundfile as sf
import numpy as np

def play_audio_file(file_path=TTS_FILE, debug=False):
    try:
        data, samplerate = sf.read(file_path)
        devices = sd.query_devices()
        device_index = None
        for i, device in enumerate(devices):
            if TTS_OUTPUT_DEVICE in device['name'] and device.get('max_output_channels', 0) > 0:
                device_index = i
                break
        if device_index is None:
            print(f"{TTS_OUTPUT_DEVICE} not found among output devices!")
            print("Available output devices:")
            for i, device in enumerate(devices):
                if device.get('max_output_channels', 0) > 0:
                    print(f"{i}: {device['name']}")
            return False

        # Normalize and amplify the audio
        max_val = np.max(np.abs(data))
        if max_val > 0:
            normalized_data = data / max_val * 0.7 * 2.0
        else:
            normalized_data = data * 2.0

        if debug:
            print(f"Playing audio to device {device_index}: {devices[device_index]['name']}")
            print(f"Sample rate: {samplerate}, Duration: {len(data)/samplerate:.2f}s")

        sd.play(normalized_data, samplerate, device=device_index)
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