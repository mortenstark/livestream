import sounddevice as sd
import soundfile as sf
import os
import datetime
import threading
import time
import numpy as np
import sys
from datetime import datetime
from config import AUDIO_INPUT_DEVICE, RECORDING_DIR

def list_audio_devices():
    """List all available audio devices with their indices."""
    devices = sd.query_devices()
    print("\nAvailable Audio Devices:")
    print("-" * 80)
    for i, device in enumerate(devices):
        io_type = []
        if device.get('max_input_channels', 0) > 0:
            io_type.append("IN")
        if device.get('max_output_channels', 0) > 0:
            io_type.append("OUT")

        io_str = ", ".join(io_type)
        print(f"{i}: {device['name']} [{io_str}] - {device.get('max_input_channels', 0)}in/{device.get('max_output_channels', 0)}out")
    print("-" * 80)
    return devices

def record_audio_from_output(output_device_name=None, duration=10, output_dir="recordings", monitor=False):
    """
    Record audio from a specified output device for a given duration.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Find the device by name
    devices = sd.query_devices()
    device_index = None

    # Print all devices for debugging
    print("\nSøger efter optagelses-device...")
    for i, device in enumerate(devices):
        if device.get('max_input_channels', 0) > 0:
            print(f"  {i}: {device['name']} (Input Channels: {device['max_input_channels']}, Default SR: {device.get('default_samplerate')})")
            if output_device_name and output_device_name in device['name']:
                print(f"    ↑ Dette matcher søgekriteriet '{output_device_name}'")
                if device_index is None:  # Vælg den første der matcher
                    device_index = i

    if device_index is None:
        print(f"❌ Kunne ikke finde input device med navn indeholdende '{output_device_name}'")
        return None

    device_info = sd.query_devices(device_index)
    print(f"\n🎙️ OPTAGER FRA: Device #{device_index}: {device_info['name']}")
    print(f"   Max input channels: {device_info['max_input_channels']}")
    print(f"   Default sample rate: {device_info['default_samplerate']} Hz")
    print(f"   Dette optager lyd FRA NotebookML via VB-Cable")

    # Set parameters - brug device'ens faktiske værdier
    channels = min(2, device_info['max_input_channels'])  # Brug max 2 kanaler (stereo)
    samplerate = int(device_info['default_samplerate'])
    print(f"   Bruger: {channels} kanaler, {samplerate} Hz")

    # Create output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"recording_{timestamp}.wav")

    # Start recording - brug den simpleste metode først
    print(f"🎙️ Optager fra '{device_info['name']}' i {duration} sekunder...")
    print(f"   Output fil: {output_file}")

    try:
        # Simpleste metode uden callback
        print("Optager... Tryk Ctrl+C for at stoppe før tid.")
        recording = sd.rec(int(samplerate * duration), samplerate=samplerate,
                          channels=channels, device=device_index, dtype='float32')

        # Vis en simpel progress bar
        for i in range(duration):
            if i > 0:
                sys.stdout.write('\r')
            sys.stdout.write(f"[{'#' * i}{' ' * (duration - i)}] {i}/{duration} sekunder")
            sys.stdout.flush()
            try:
                sd.sleep(1000)  # Vent 1 sekund
            except KeyboardInterrupt:
                print("\nOptagelse stoppet før tid.")
                break

        print("\nVenter på at optagelsen afsluttes...")
        sd.wait()  # Vent til optagelsen er færdig

        # Save the recording
        sf.write(output_file, recording, samplerate)
        print(f"✅ Optagelse gemt som {output_file}")
        return output_file

    except Exception as e:
        print(f"Fejl under optagelse: {e}")
        print("Prøver alternativ optagelsesmetode...")

        try:
            # Alternativ metode med manuel optagelse
            recording = np.zeros((samplerate * duration, channels), dtype='float32')
            with sd.InputStream(samplerate=samplerate, device=device_index,
                              channels=channels, dtype='float32') as stream:

                for i in range(duration):
                    data, overflowed = stream.read(samplerate)
                    start_idx = i * samplerate
                    end_idx = min((i + 1) * samplerate, len(recording))
                    recording[start_idx:end_idx] = data[:end_idx-start_idx]

                    sys.stdout.write(f"\rOptager: {i+1}/{duration} sekunder")
                    sys.stdout.flush()

            print("\nOptagelse fuldført.")

            # Save the recording
            sf.write(output_file, recording, samplerate)
            print(f"✅ Optagelse gemt som {output_file}")
            return output_file

        except Exception as e2:
            print(f"Alternativ metode fejlede også: {e2}")
            return None

def start_recording_after_playback(playback_function, playback_args=None,
                                  recording_duration=10,
                                  output_dir=RECORDING_DIR,
                                  output_device_name=AUDIO_INPUT_DEVICE,
                                  delay_after_playback=0.5,
                                  monitor=False):
    """
    Afspiller en lydfil og starter optagelse EFTER afspilningen er færdig.

    Args:
        playback_function: Funktionen der afspiller lyden (f.eks. play_audio_file)
        playback_args: Argumenter til afspilningsfunktionen (f.eks. filsti)
        recording_duration: Varighed af optagelsen i sekunder
        output_dir: Mappe til at gemme optagelsen
        output_device_name: Navn på output-enheden der skal optages fra
        delay_after_playback: Forsinkelse i sekunder mellem afspilning og optagelse
        monitor: Whether to show real-time level monitoring

    Returns:
        str: Sti til den gemte lydfil, eller None hvis optagelsen fejlede
    """
    # Play the audio file
    print("🔊 Afspiller lydfil...")
    if isinstance(playback_args, dict):
        playback_function(**playback_args)
    elif playback_args is not None:
        playback_function(playback_args)
    else:
        playback_function()

    # Wait briefly to ensure playback is completely finished
    print(f"⏱️ Venter {delay_after_playback} sekunder efter afspilning...")
    time.sleep(delay_after_playback)

    # Start recording
    print("🎙️ Starter optagelse af svar...")
    return record_audio_from_output(
        output_device_name=output_device_name,
        duration=recording_duration,
        output_dir=output_dir,
        monitor=monitor
    )

# Eksempel på brug:
if __name__ == "__main__":
    import argparse
    from audio import play_audio_file

    # Forsøg at importere TTS_FILE fra config, men fortsæt hvis det fejler
    try:
        from config import TTS_FILE
    except ImportError:
        try:
            from config import TTS_FILE_PATH as TTS_FILE
        except ImportError:
            TTS_FILE = "graham.wav"  # Fallback

    parser = argparse.ArgumentParser(description="Audio recording utility for NotebookML")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List devices command
    list_parser = subparsers.add_parser("list", help="List all audio devices")

    # Record command
    record_parser = subparsers.add_parser("record", help="Record audio from a device")
    record_parser.add_argument("--device", help="Device name to record from", default=AUDIO_INPUT_DEVICE)
    record_parser.add_argument("--duration", type=int, default=10, help="Recording duration in seconds")
    record_parser.add_argument("--monitor", action="store_true", help="Show level monitoring")

    # Play and record command
    playrecord_parser = subparsers.add_parser("playrecord", help="Play audio and then record")
    playrecord_parser.add_argument("file", nargs="?", default=TTS_FILE, help="Audio file to play")
    playrecord_parser.add_argument("--duration", type=int, default=10, help="Recording duration in seconds")
    playrecord_parser.add_argument("--delay", type=float, default=0.5, help="Delay after playback")
    playrecord_parser.add_argument("--monitor", action="store_true", help="Show level monitoring")

    args = parser.parse_args()

    if args.command == "list":
        list_audio_devices()
    elif args.command == "record":
        record_audio_from_output(
            output_device_name=args.device,
            duration=args.duration,
            monitor=args.monitor
        )
    elif args.command == "playrecord":
        start_recording_after_playback(
            playback_function=play_audio_file,
            playback_args=args.file,
            recording_duration=args.duration,
            delay_after_playback=args.delay,
            monitor=args.monitor
        )
    else:
        # Default behavior if no command is specified
        list_audio_devices()
        parser.print_help()