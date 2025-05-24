import numpy as np
import sounddevice as sd
import soundfile as sf
import sys
from config import TTS_OUTPUT_DEVICE, AUDIO_DEVICE_INDEX, DEFAULT_GAIN

def list_audio_devices():
    """List all available audio devices with their IDs and channels"""
    devices = sd.query_devices()
    
    print("\n=== AUDIO DEVICES ===")
    print(f"{'ID':<4} {'Name':<40} {'In':<4} {'Out':<4} {'Default':<8}")
    print("-" * 65)
    
    default_input = sd.query_devices(kind='input')
    default_output = sd.query_devices(kind='output')
    
    for i, device in enumerate(devices):
        is_default = ""
        if device['name'] == default_input['name'] and device['hostapi'] == default_input['hostapi']:
            is_default += "IN "
        if device['name'] == default_output['name'] and device['hostapi'] == default_output['hostapi']:
            is_default += "OUT"
        
        print(f"{i:<4} {device['name'][:39]:<40} {device['max_input_channels']:<4} "
              f"{device['max_output_channels']:<4} {is_default:<8}")
    
    # Look for VB-Cable devices
    vb_devices = [i for i, d in enumerate(devices) if 'CABLE' in d['name']]
    if vb_devices:
        print("\nVB-CABLE DEVICES:")
        for dev_id in vb_devices:
            device = devices[dev_id]
            print(f"ID {dev_id}: {device['name']} (In: {device['max_input_channels']}, Out: {device['max_output_channels']})")
    else:
        print("\nNo VB-Cable devices found!")
    
    return devices

def play_audio_file(file_path, device_index=None, gain=DEFAULT_GAIN, monitor=False, debug=False):
    """
    Play an audio file to a specific output device with gain control and level monitoring.
    """
    try:
        # Find the device by index or name
        devices = sd.query_devices()

        if device_index is None:
            # Try to use the configured device index first
            if AUDIO_DEVICE_INDEX is not None:
                device_index = AUDIO_DEVICE_INDEX
            else:
                # Fall back to searching by name
                for i, device in enumerate(devices):
                    if TTS_OUTPUT_DEVICE in device['name'] and device.get('max_output_channels', 0) > 0:
                        # Prioriter 2-kanals versionen
                        if device.get('max_output_channels', 0) == 2:
                            device_index = i
                            break

        if device_index is None:
            print(f"{TTS_OUTPUT_DEVICE} not found among output devices!")
            print("Available output devices:")
            list_audio_devices()
            return False

        device_info = sd.query_devices(device_index)
        print(f"\n🔊 Device #{device_index}: {device_info['name']}")
        print(f"   Max output channels: {device_info['max_output_channels']}")
        max_channels = device_info['max_output_channels']

        # Load audio file
        data, samplerate = sf.read(file_path)
        print(f"📊 Audio file: {file_path}")
        print(f"   Shape: {data.shape}, Type: {data.dtype}, Rate: {samplerate}Hz")

        # Apply gain to increase volume if needed
        if gain != 1.0:
            print(f"🔊 Applying gain: {gain}x")
            data = data * gain
            data = np.clip(data, -1.0, 1.0)  # Prevent distortion

        # Handle channels correctly
        if data.ndim > 1:
            original_channels = data.shape[1]
            if original_channels > max_channels:
                print(f"🎧 Downmixing from {original_channels} to {max_channels} channels")
                if max_channels == 1:
                    data = np.mean(data, axis=1)
                else:
                    # Keep only the channels we need
                    data = data[:, :max_channels]
        elif data.ndim == 1 and max_channels > 1:
            # Mono to stereo/multi-channel conversion
            print(f"🎧 Upmixing from mono to {max_channels} channels")
            data = np.tile(data.reshape(-1, 1), (1, max_channels))

        # Ensure compatible data type
        data = data.astype(np.float32)

        # Print final data shape
        if data.ndim > 1:
            print(f"🔄 Final audio format: {data.shape[1]} channels, {len(data)} samples")
        else:
            print(f"🔄 Final audio format: 1 channel, {len(data)} samples")

        # Play the audio
        try:
            if monitor:
                def callback(outdata, frames, time, status):
                    if status:
                        print(f"Status: {status}")
                    if outdata.size > 0:
                        level = np.sqrt(np.mean(outdata**2))
                        bars = int(level * 50)
                        sys.stdout.write('\r[' + '█' * bars + ' ' * (50 - bars) + f'] {level:.3f}')
                        sys.stdout.flush()
                with sd.OutputStream(
                    samplerate=samplerate,
                    device=device_index,
                    channels=max_channels,
                    callback=callback
                ):
                    sd.play(data, samplerate, device=device_index, blocking=True)
                    sys.stdout.write('\n')  # New line after level display
            else:
                print("▶️ Starting playback...")
                sd.play(data, samplerate, device=device_index)
                sd.wait()
                print("✅ Playback complete.")
            return True
        except Exception as e:
            print(f"❌ Playback error: {e}")
            import traceback
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"❌ Error playing audio: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_test_tone(frequency=440, duration=3, device_index=None, gain=1.0):
    """Generate and play a test tone to verify audio routing."""
    try:
        # Create a sine wave test tone
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        tone = 0.5 * np.sin(2 * np.pi * frequency * t)

        # Find the device
        devices = sd.query_devices()
        if device_index is None:
            # Try to use the configured device index first
            if AUDIO_DEVICE_INDEX is not None:
                device_index = AUDIO_DEVICE_INDEX
            else:
                # Fall back to searching by name
                for i, device in enumerate(devices):
                    if TTS_OUTPUT_DEVICE in device['name'] and device.get('max_output_channels', 0) > 0:
                        device_index = i
                        break

        if device_index is None:
            print(f"{TTS_OUTPUT_DEVICE} not found among output devices!")
            list_audio_devices()
            return False

        # Get the device's channel count
        max_channels = devices[device_index].get('max_output_channels', 2)

        # Convert mono to stereo if needed
        if tone.ndim == 1 and max_channels > 1:
            tone = np.tile(tone.reshape(-1, 1), (1, max_channels))

        # Apply gain
        tone = tone * gain

        print(f"🎵 Playing {frequency}Hz test tone at {gain*100:.0f}% amplitude")
        print(f"   Duration: {duration} seconds, Sample rate: {sample_rate}Hz")
        print(f"\n🔊 Device #{device_index}: {devices[device_index]['name']}")

        # Play the tone
        sd.play(tone, sample_rate, device=device_index)
        
        # Show a progress bar
        for i in range(int(duration)):
            progress = int(30 * (i+1) / duration)
            sys.stdout.write(f"\r[{'#' * progress}{' ' * (30-progress)}] {i+1}/{int(duration)}s")
            sys.stdout.flush()
            import time
            time.sleep(1)
        
        sd.stop()
        print("\n✅ Test tone complete.")
        return True

    except Exception as e:
        print(f"❌ Test tone error: {e}")
        return False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Audio playback utility for NotebookML")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List devices command
    list_parser = subparsers.add_parser("list", help="List all audio devices")

    # Play audio command
    play_parser = subparsers.add_parser("play", help="Play an audio file")
    play_parser.add_argument("file", help="Audio file to play")
    play_parser.add_argument("--device", type=int, help="Device index to play to")
    play_parser.add_argument("--gain", type=float, default=DEFAULT_GAIN, help="Volume multiplier")
    play_parser.add_argument("--monitor", action="store_true", help="Show level monitoring")
    play_parser.add_argument("--debug", action="store_true", help="Show debug information")

    # Test tone command
    tone_parser = subparsers.add_parser("tone", help="Play a test tone")
    tone_parser.add_argument("--freq", type=int, default=440, help="Frequency in Hz")
    tone_parser.add_argument("--duration", type=float, default=3, help="Duration in seconds")
    tone_parser.add_argument("--device", type=int, help="Device index to play to")
    tone_parser.add_argument("--gain", type=float, default=1.0, help="Volume multiplier")

    args = parser.parse_args()

    if args.command == "list":
        list_audio_devices()
    elif args.command == "play":
        play_audio_file(
            file_path=args.file,
            device_index=args.device,
            gain=args.gain,
            monitor=args.monitor,
            debug=args.debug
        )
    elif args.command == "tone":
        generate_test_tone(
            frequency=args.freq,
            duration=args.duration,
            device_index=args.device,
            gain=args.gain
        )
    else:
        # Default behavior if no command is specified
        list_audio_devices()
        parser.print_help()