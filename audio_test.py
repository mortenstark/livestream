#!/usr/bin/env python3
import argparse
import sounddevice as sd
import soundfile as sf
import numpy as np
import sys
import time
import os

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

def play_audio_file(file_path, device_index=None, gain=3.0, monitor=False, debug=False):
    """
    Play an audio file to a specific output device with gain control and level monitoring.

    Args:
        file_path (str): Path to the audio file to play
        device_index (int): Index of the output device
        gain (float): Volume multiplier (1.0 = original volume)
        monitor (bool): Whether to show real-time level monitoring
        debug (bool): Whether to print debug information

    Returns:
        bool: True if playback was successful, False otherwise
    """
    try:
        # Load the audio file
        data, samplerate = sf.read(file_path)

        # Find the device
        devices = sd.query_devices()

        if device_index is None:
            print("No device specified. Please provide a device index.")
            list_audio_devices()
            return False

        # Get the device's channel count
        max_channels = devices[device_index].get('max_output_channels', 2)

        # Convert mono to stereo if needed
        if data.ndim == 1 and max_channels > 1:
            data = np.tile(data.reshape(-1, 1), (1, max_channels))

        # Apply gain to increase volume
        data = data * gain
        data = np.clip(data, -1.0, 1.0)  # Prevent distortion

        if debug:
            print(f"Playing audio to device {device_index}: {devices[device_index]['name']}")
            print(f"Sample rate: {samplerate}, Duration: {len(data)/samplerate:.2f}s")
            print(f"Channels: {data.shape[1] if data.ndim > 1 else 1}, Gain: {gain}x")

        # Create a callback for level monitoring if requested
        if monitor:
            def callback(outdata, frames, time, status):
                if status:
                    print(f"Status: {status}")

                # Calculate RMS level for monitoring
                if outdata.size > 0:
                    level = np.sqrt(np.mean(outdata**2))
                    bars = int(level * 50)
                    sys.stdout.write('\r[' + '█' * bars + ' ' * (50 - bars) + f'] {level:.3f}')
                    sys.stdout.flush()

            # Start the stream with callback
            with sd.OutputStream(
                samplerate=samplerate,
                device=device_index,
                channels=max_channels,
                callback=callback
            ):
                sd.play(data, samplerate, device=device_index, blocking=True)
                sys.stdout.write('\n')  # New line after level display
        else:
            # Simple playback without monitoring
            sd.play(data, samplerate, device=device_index)
            sd.wait()

        if debug:
            print("Audio playback completed")
        return True

    except Exception as e:
        print(f"Error playing audio: {e}")
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
            print("No device specified. Please provide a device index.")
            list_audio_devices()
            return False

        # Get the device's channel count
        max_channels = devices[device_index].get('max_output_channels', 2)

        # Convert mono to stereo if needed
        if tone.ndim == 1 and max_channels > 1:
            tone = np.tile(tone.reshape(-1, 1), (1, max_channels))

        # Apply gain
        tone = tone * gain

        print(f"Playing {frequency}Hz test tone to device {device_index}: {devices[device_index]['name']}")

        # Play the tone
        sd.play(tone, sample_rate, device=device_index)
        sd.wait()
        print("Test tone playback completed")
        return True

    except Exception as e:
        print(f"Error playing test tone: {e}")
        return False

def record_audio(device_index=None, duration=10, output_file=None, monitor=False):
    """Record audio from a specific input device."""
    try:
        # Find the device
        devices = sd.query_devices()

        if device_index is None:
            print("No device specified. Please provide a device index.")
            list_audio_devices()
            return False

        # Get the device's sample rate and channel count
        samplerate = int(devices[device_index]['default_samplerate'])
        channels = min(2, devices[device_index]['max_input_channels'])

        print(f"Recording from device {device_index}: {devices[device_index]['name']}")
        print(f"Sample rate: {samplerate}, Channels: {channels}, Duration: {duration}s")

        # Generate output filename if not provided
        if output_file is None:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            output_file = f"recording_{timestamp}.wav"

        # Create a callback for level monitoring if requested
        if monitor:
            # Create a buffer to store the recording
            frames = []

            def callback(indata, frame_count, time_info, status):
                if status:
                    print(f"Status: {status}")

                # Store the data
                frames.append(indata.copy())

                # Calculate RMS level for monitoring
                if indata.size > 0:
                    level = np.sqrt(np.mean(indata**2))
                    bars = int(level * 50)
                    sys.stdout.write('\r[' + '█' * bars + ' ' * (50 - bars) + f'] {level:.3f}')
                    sys.stdout.flush()

            # Record with callback
            with sd.InputStream(samplerate=samplerate, device=device_index, 
                              channels=channels, callback=callback):
                print("Recording started. Press Ctrl+C to stop early.")
                sd.sleep(int(duration * 1000))
                sys.stdout.write('\n')  # New line after level display

            # Combine all frames into a single array
            recording = np.concatenate(frames, axis=0)
        else:
            # Simple recording without monitoring
            recording = sd.rec(int(duration * samplerate), samplerate=samplerate, 
                             channels=channels, device=device_index)
            sd.wait()  # Wait until the recording is finished

        # Save the recording to a .wav file
        sf.write(output_file, recording, samplerate)
        print(f"Recording saved to: {output_file}")
        return True

    except Exception as e:
        print(f"Error recording audio: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_audio_chain(playback_device=None, recording_device=None, test_file=None, gain=3.0, duration=10):
    """Test the complete audio chain by playing and recording simultaneously."""
    try:
        # Find the devices
        devices = sd.query_devices()

        if playback_device is None or recording_device is None:
            print("Both playback and recording devices must be specified.")
            list_audio_devices()
            return False

        # Generate a test tone file if no file is provided
        if test_file is None or not os.path.exists(test_file):
            print("Generating test tone file...")
            sample_rate = 44100
            t = np.linspace(0, 5, int(sample_rate * 5), False)
            tone = 0.5 * np.sin(2 * np.pi * 440 * t)
            test_file = "test_tone.wav"
            sf.write(test_file, tone, sample_rate)

        # Load the audio file
        data, samplerate = sf.read(test_file)

        # Get the playback device's channel count
        max_channels = devices[playback_device].get('max_output_channels', 2)

        # Convert mono to stereo if needed
        if data.ndim == 1 and max_channels > 1:
            data = np.tile(data.reshape(-1, 1), (1, max_channels))

        # Apply gain
        data = data * gain
        data = np.clip(data, -1.0, 1.0)  # Prevent distortion

        # Get the recording device's sample rate and channel count
        rec_samplerate = int(devices[recording_device]['default_samplerate'])
        rec_channels = min(2, devices[recording_device]['max_input_channels'])

        # Generate output filename
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        output_file = f"chain_test_{timestamp}.wav"

        # Create buffers for recording
        frames = []

        # Create callbacks
        def input_callback(indata, frame_count, time_info, status):
            if status:
                print(f"Input status: {status}")
            frames.append(indata.copy())

            # Calculate RMS level for monitoring
            if indata.size > 0:
                level = np.sqrt(np.mean(indata**2))
                bars = int(level * 50)
                sys.stdout.write('\r[' + '█' * bars + ' ' * (50 - bars) + f'] {level:.3f}')
                sys.stdout.flush()

        # Start recording
        with sd.InputStream(samplerate=rec_samplerate, device=recording_device,
                          channels=rec_channels, callback=input_callback):
            print(f"Recording from device {recording_device}: {devices[recording_device]['name']}")

            # Wait a moment before playing
            time.sleep(1)

            # Play the audio
            print(f"Playing to device {playback_device}: {devices[playback_device]['name']}")
            sd.play(data, samplerate, device=playback_device)
            sd.wait()

            # Continue recording for a bit after playback
            print("Continuing to record...")
            time.sleep(2)
            sys.stdout.write('\n')  # New line after level display

        # Combine all frames into a single array
        recording = np.concatenate(frames, axis=0)

        # Save the recording
        sf.write(output_file, recording, rec_samplerate)
        print(f"Test recording saved to: {output_file}")
        return True

    except Exception as e:
        print(f"Error testing audio chain: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audio testing utility for NotebookML")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List devices command
    list_parser = subparsers.add_parser("list", help="List all audio devices")

    # Play audio command
    play_parser = subparsers.add_parser("play", help="Play an audio file")
    play_parser.add_argument("file", help="Audio file to play")
    play_parser.add_argument("--device", type=int, required=True, help="Device index to play to")
    play_parser.add_argument("--gain", type=float, default=3.0, help="Volume multiplier")
    play_parser.add_argument("--monitor", action="store_true", help="Show level monitoring")
    play_parser.add_argument("--debug", action="store_true", help="Show debug information")

    # Test tone command
    tone_parser = subparsers.add_parser("tone", help="Play a test tone")
    tone_parser.add_argument("--freq", type=int, default=440, help="Frequency in Hz")
    tone_parser.add_argument("--duration", type=float, default=3, help="Duration in seconds")
    tone_parser.add_argument("--device", type=int, required=True, help="Device index to play to")
    tone_parser.add_argument("--gain", type=float, default=1.0, help="Volume multiplier")

    # Record command
    record_parser = subparsers.add_parser("record", help="Record audio from a device")
    record_parser.add_argument("--device", type=int, required=True, help="Device index to record from")
    record_parser.add_argument("--duration", type=int, default=10, help="Recording duration in seconds")
    record_parser.add_argument("--output", help="Output file name")
    record_parser.add_argument("--monitor", action="store_true", help="Show level monitoring")

    # Test chain command
    chain_parser = subparsers.add_parser("chain", help="Test the complete audio chain")
    chain_parser.add_argument("--playback", type=int, required=True, help="Playback device index")
    chain_parser.add_argument("--recording", type=int, required=True, help="Recording device index")
    chain_parser.add_argument("--file", help="Audio file to play (optional)")
    chain_parser.add_argument("--gain", type=float, default=3.0, help="Volume multiplier")
    chain_parser.add_argument("--duration", type=int, default=10, help="Total test duration in seconds")

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
    elif args.command == "record":
        record_audio(
            device_index=args.device,
            duration=args.duration,
            output_file=args.output,
            monitor=args.monitor
        )
    elif args.command == "chain":
        test_audio_chain(
            playback_device=args.playback,
            recording_device=args.recording,
            test_file=args.file,
            gain=args.gain,
            duration=args.duration
        )
    else:
        parser.print_help()
