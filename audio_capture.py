import sounddevice as sd
import soundfile as sf
import os
import datetime
import threading
import time

def record_audio_from_output(output_device_name="CABLE Output (VB-Audio Virtual Cable)", 
                            duration=60, 
                            output_dir="recordings",
                            wait_for_playback=False):
    """
    Record audio from a specified output device and save it as a .wav file.

    Args:
    output_device_name (str): Name of the output device to record from.
    duration (int): Duration of the recording in seconds.
    output_dir (str): Directory to save the recorded .wav file.
    wait_for_playback (bool): If True, wait for playback to finish before starting recording.

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

def start_recording_after_playback(playback_function, playback_args=None, 
                                  recording_duration=60, 
                                  output_dir="recordings",
                                  output_device_name="CABLE Output (VB-Audio Virtual Cable)",
                                  delay_after_playback=0.5):
    """
    Afspiller en lydfil og starter optagelse EFTER afspilningen er færdig.
    
    Args:
        playback_function: Funktionen der afspiller lyden (f.eks. play_audio_file)
        playback_args: Argumenter til afspilningsfunktionen (f.eks. filsti)
        recording_duration: Varighed af optagelsen i sekunder
        output_dir: Mappe til at gemme optagelsen
        output_device_name: Navn på output-enheden der skal optages fra
        delay_after_playback: Forsinkelse i sekunder mellem afspilning og optagelse
        
    Returns:
        str: Sti til den gemte lydfil, eller None hvis optagelsen fejlede
    """
    # Afspil lydfilen
    print("🔊 Afspiller lydfil...")
    if playback_args:
        playback_function(playback_args)
    else:
        playback_function()
    
    # Vent kort tid for at sikre afspilningen er helt færdig
    print(f"⏱️ Venter {delay_after_playback} sekunder efter afspilning...")
    time.sleep(delay_after_playback)
    
    # Start optagelse
    print("🎙️ Starter optagelse af svar...")
    return record_audio_from_output(
        output_device_name=output_device_name,
        duration=recording_duration,
        output_dir=output_dir
    )

# Eksempel på brug:
if __name__ == "__main__":
    from audio import play_audio_file
    from config import TTS_FILE
    
    output_file = start_recording_after_playback(
        playback_function=play_audio_file,
        playback_args=TTS_FILE,
        recording_duration=30,
        delay_after_playback=0.5
    )
    
    print(f"Optagelse gemt som: {output_file}")