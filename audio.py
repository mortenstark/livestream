from config import TTS_FILE
import time

def play_audio_file(file_path=TTS_FILE, debug=False):
    """Play an audio file using Python with higher volume"""
    try:
        import sounddevice as sd
        import soundfile as sf
        import numpy as np

        # Load the audio file
        data, samplerate = sf.read(file_path)
        print(f"Loaded audio file: {file_path}, Sample rate: {samplerate}, Duration: {len(data)/samplerate:.2f}s")

        # Get the list of audio devices
        devices = sd.query_devices()

        # Print all available audio devices only in debug mode
        if debug:
            print("\nAll available audio devices:")
            for i, device in enumerate(devices):
                output_channels = device.get('max_output_channels', 0)
                input_channels = device.get('max_input_channels', 0)
                device_info = []
                if output_channels > 0:
                    device_info.append(f"Output: {output_channels} ch")
                if input_channels > 0:
                    device_info.append(f"Input: {input_channels} ch")
                print(f"{i}: {device['name']} ({', '.join(device_info)})")
            print()

        # Find the CABLE Input device
        cable_device = None
        for i, device in enumerate(devices):
            if "CABLE Input" in device['name'] and device.get('max_output_channels', 0) > 0:
                cable_device = i
                break

        if cable_device is None:
            print("CABLE Input device not found")
            return False

        print(f"Playing audio to device {cable_device}: {devices[cable_device]['name']}")
        print(f"Device details: {devices[cable_device]}")

        # Normalize and amplify the audio
        max_val = np.max(np.abs(data))
        if max_val > 0:
            # Normalize to -3dB and amplify by 2x
            normalized_data = data / max_val * 0.7 * 2.0
        else:
            normalized_data = data * 2.0

        # Play the audio file
        print("Playing audio...")
        sd.play(normalized_data, samplerate, device=cable_device)
        sd.wait()  # Wait until the audio is finished
        print("Audio playback completed")
        return True
    except Exception as e:
        print(f"Error playing audio: {e}")
        import traceback
        traceback.print_exc()
        return False