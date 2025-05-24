# test_audio_simple_fixed.py
import os
import time
from audio import list_audio_devices
import sounddevice as sd
import numpy as np

def main():
    print("=== SIMPEL AUDIO TEST ===")
    print("Denne test vil afspille lyd til VB-Cable")

    # List alle audio devices
    print("\nLister alle audio devices:")
    devices = list_audio_devices()

    # Find CABLE Input device
    cable_input_index = None
    for i, device in enumerate(devices):
        if "CABLE Input" in device['name'] and device.get('max_output_channels', 0) > 0:
            cable_input_index = i
            print(f"\nFandt CABLE Input på device index {i}")
            print(f"Supported sample rates: {device.get('default_samplerate', 'Unknown')}")
            break

    if cable_input_index is None:
        print("\nKunne ikke finde CABLE Input device!")
        return

    # Få device info
    device_info = sd.query_devices(cable_input_index)
    sample_rate = int(device_info.get('default_samplerate', 48000))
    print(f"Bruger sample rate: {sample_rate} Hz")

    # Test med en tone først
    print("\n=== TEST 1: Afspiller testtone ===")
    print(f"Afspiller 440Hz tone til device {cable_input_index}")

    try:
        # Generer en simpel tone
        duration = 3  # sekunder
        frequency = 440  # Hz
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        tone = 0.5 * np.sin(2 * np.pi * frequency * t)

        # Konverter til stereo hvis nødvendigt
        channels = device_info.get('max_output_channels', 2)
        if channels > 1:
            tone = np.tile(tone.reshape(-1, 1), (1, channels))

        # Afspil tonen
        print(f"Afspiller {frequency}Hz tone i {duration} sekunder...")
        sd.play(tone, sample_rate, device=cable_input_index)
        sd.wait()
        print("Tone afspillet!")
    except Exception as e:
        print(f"Fejl ved afspilning af testtone: {e}")
        import traceback
        traceback.print_exc()
        return

    # Vent lidt
    print("\nVenter 2 sekunder...")
    time.sleep(2)

    # Test med en lydfil
    print("\n=== TEST 2: Afspiller lydfil ===")
    # Antager at graham.wav findes i samme mappe
    file_path = "graham.wav"
    if not os.path.exists(file_path):
        print(f"Kunne ikke finde {file_path}!")
        return

    try:
        import soundfile as sf

        # Indlæs lydfilen
        data, file_samplerate = sf.read(file_path)
        print(f"Lydfil: {file_path}")
        print(f"Sample rate: {file_samplerate} Hz")
        print(f"Kanaler: {data.shape[1] if len(data.shape) > 1 else 1}")

        # Konverter til stereo hvis nødvendigt
        if len(data.shape) == 1 and channels > 1:
            data = np.tile(data.reshape(-1, 1), (1, channels))
        elif len(data.shape) > 1 and data.shape[1] > channels:
            data = data[:, :channels]

        # Anvend gain
        gain = 3.0
        data = data * gain
        data = np.clip(data, -1.0, 1.0)  # Undgå forvrængning

        # Afspil lydfilen
        print(f"Afspiller {file_path} med gain {gain}...")
        sd.play(data, file_samplerate, device=cable_input_index)
        sd.wait()
        print("Lydfil afspillet!")
    except Exception as e:
        print(f"Fejl ved afspilning af lydfil: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n=== TEST GENNEMFØRT ===")
    print("Hvis du kunne høre lyden gennem VB-Cable, virker det!")
    print("Tjek om NotebookLM reagerede på lyden.")

if __name__ == "__main__":
    main()