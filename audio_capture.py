import sounddevice as sd
import soundfile as sf
import os
import datetime

def record_audio_from_output(output_device_name="CABLE Output (VB-Audio Virtual Cable)", duration=60, output_dir="recordings"):
    """
    Record audio from a specified output device and save it as a .wav file.

    Args:
        output_device_name (str): Name of the output device to record from.
        duration (int): Duration of the recording in seconds.
        output_dir (str): Directory to save the recorded .wav file.

    Returns:
        str: Path to the saved .wav file, or None if recording failed.
    """
    try:
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Find the output device by name
        devices = sd.query_devices()
        output_device_index = None
        for i, device in enumerate(devices):
            if output_device_name in device['name'] and device['max_input_channels'] > 0:
                output_device_index = i
                break

        if output_device_index is None:
            print(f"Output device '{output_device_name}' not found.")
            return None

        # Set the default input device to the selected output device
        sd.default.device = (output_device_index, None)

        # Get the sample rate of the device
        samplerate = int(devices[output_device_index]['default_samplerate'])

        # Prepare the output file path
        timestamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
        output_file = os.path.join(output_dir, f"notebookml_audio_{timestamp}.wav")

        print(f"🎙️ Recording audio from '{output_device_name}' for {duration} seconds...")
        print(f"🎚️ Using sample rate: {samplerate}")

        # Record the audio
        recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)
        sd.wait()  # Wait until the recording is finished

        # Save the recording to a .wav file
        sf.write(output_file, recording, samplerate)
        print(f"✅ Audio saved to: {output_file}")

        return output_file

    except Exception as e:
        print(f"❌ Error during recording: {e}")
        return None