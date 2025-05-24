import numpy as np
import sounddevice as sd
import soundfile as sf
import argparse
import time
import sys

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

def play_audio(filename, device_id, monitor=False, gain=1.0):
    """Play audio file to specified device with proper channel handling"""
    try:
        device_info = sd.query_devices(device_id)
        print(f"\n🔊 Device #{device_id}: {device_info['name']}")
        print(f"   Max output channels: {device_info['max_output_channels']}")
        max_channels = device_info['max_output_channels']
    except Exception as e:
        print(f"⚠️ Could not find device ID #{device_id}: {e}")
        raise

    # Load audio file
    try:
        data, samplerate = sf.read(filename)
        print(f"📊 Audio file: {filename}")
        print(f"   Shape: {data.shape}, Type: {data.dtype}, Rate: {samplerate}Hz")
    except Exception as e:
        print(f"❌ Error loading audio file: {e}")
        raise

    # Apply gain to increase volume if needed
    if gain != 1.0:
        print(f"🔊 Applying gain: {gain}x")
        data = data * gain
        # Clip to prevent distortion
        data = np.clip(data, -1.0, 1.0)

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
            monitor_levels(data, samplerate, device_id, duration=len(data)/samplerate)
        else:
            print("▶️ Starting playback...")
            sd.play(data, samplerate, device=device_id)
            sd.wait()
        print("✅ Playback complete.")
    except Exception as e:
        print(f"❌ Playback error: {e}")
        raise

def monitor_levels(data, samplerate, device_id, duration):
    """Monitor audio levels during playback with a simple VU meter"""
    # Start playback in non-blocking mode
    sd.play(data, samplerate, device=device_id)
    
    # Calculate frames per update
    update_interval = 0.05  # seconds
    
    # Monitor levels
    start_time = time.time()
    print("▶️ Playing with level monitoring:")
    
    while time.time() - start_time < duration:
        current_time = time.time() - start_time
        current_frame = int(current_time * samplerate)
        
        if current_frame < len(data):
            # Get current audio level
            if data.ndim > 1:
                # For multi-channel, take max across all channels
                frame_data = data[max(0, current_frame-100):min(len(data), current_frame+100)]
                level = np.max(np.abs(frame_data))
            else:
                # For mono
                frame_data = data[max(0, current_frame-100):min(len(data), current_frame+100)]
                level = np.max(np.abs(frame_data))
            
            # Print a simple VU meter
            bars = int(level * 50)
            sys.stdout.write('\r[' + '█' * bars + ' ' * (50 - bars) + f'] {level:.3f} ({current_time:.1f}s)')
            sys.stdout.flush()
        
        time.sleep(update_interval)
    
    print("\nWaiting for playback to complete...")
    sd.wait()

def play_test_tone(device_id, duration=10, frequency=440, amplitude=0.5):
    """Play a continuous test tone to verify audio routing"""
    try:
        device_info = sd.query_devices(device_id)
        print(f"\n🔊 Device #{device_id}: {device_info['name']}")
        print(f"   Max output channels: {device_info['max_output_channels']}")
        channels = device_info['max_output_channels']
    except Exception as e:
        print(f"⚠️ Could not find device ID #{device_id}: {e}")
        raise
    
    sample_rate = 48000
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = amplitude * np.sin(2 * np.pi * frequency * t)
    
    # Convert to stereo/multi-channel if needed
    if channels > 1:
        tone = np.tile(tone.reshape(-1, 1), (1, min(channels, 2)))
    
    print(f"🎵 Playing {frequency}Hz test tone at {amplitude*100:.0f}% amplitude")
    print(f"   Duration: {duration} seconds, Sample rate: {sample_rate}Hz")
    
    # Play the tone
    try:
        sd.play(tone, sample_rate, device=device_id)
        
        # Show a progress bar
        for i in range(duration):
            progress = int(30 * (i+1) / duration)
            sys.stdout.write(f"\r[{'#' * progress}{' ' * (30-progress)}] {i+1}/{duration}s")
            sys.stdout.flush()
            time.sleep(1)
        
        sd.stop()
        print("\n✅ Test tone complete.")
    except Exception as e:
        print(f"❌ Test tone error: {e}")
        raise

def test_audio_routing(input_file, output_device_id):
    """Test the audio routing path (without recording)"""
    print("\n🧪 TESTING AUDIO ROUTING 🧪")
    print("=" * 50)
    
    # Play audio to VB-Cable Input
    print("\n📤 Playing audio to VB-Cable Input")
    play_audio(input_file, output_device_id, monitor=True, gain=2.0)
    
    print("\n🏁 TEST COMPLETE 🏁")
    print("\n📋 NEXT STEPS:")
    print("1. Check if NotebookML is receiving audio")
    print("2. Make sure Chrome's microphone is set to 'CABLE Output'")
    print("3. If no response, try the test tone with higher amplitude")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audio routing test tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # List command
    list_parser = subparsers.add_parser("list", help="List audio devices")

    # Play command
    play_parser = subparsers.add_parser("play", help="Play audio file")
    play_parser.add_argument("filename", help="Audio file to play")
    play_parser.add_argument("--device", type=int, required=True, help="Output device ID")
    play_parser.add_argument("--monitor", action="store_true", help="Monitor audio levels")
    play_parser.add_argument("--gain", type=float, default=1.0, help="Volume gain multiplier")

    # Test command
    test_parser = subparsers.add_parser("test", help="Test audio routing")
    test_parser.add_argument("filename", help="Audio file to play")
    test_parser.add_argument("--output", type=int, required=True, help="Output device ID (CABLE Input)")

    # Tone command
    tone_parser = subparsers.add_parser("tone", help="Play test tone")
    tone_parser.add_argument("--device", type=int, required=True, help="Output device ID")
    tone_parser.add_argument("--duration", type=int, default=30, help="Duration in seconds")
    tone_parser.add_argument("--frequency", type=int, default=440, help="Tone frequency in Hz")
    tone_parser.add_argument("--amplitude", type=float, default=0.8, help="Tone amplitude (0.0-1.0)")

    args = parser.parse_args()

    if args.command == "list":
        list_audio_devices()
    elif args.command == "play":
        play_audio(args.filename, args.device, args.monitor, args.gain)
    elif args.command == "test":
        test_audio_routing(args.filename, args.output)
    elif args.command == "tone":
        play_test_tone(args.device, args.duration, args.frequency, args.amplitude)
    else:
        list_audio_devices()
        parser.print_help()

# Print a message about the updated script
print("\n✨ UPDATED AUDIO TEST SCRIPT ✨")
print("This script now includes:")
print("- Audio file playback with gain control")
print("- Test tone generation")
print("- No recording functionality (focus on sending audio)")
print("- Improved command-line interface")
print("\nRun 'python audio_test.py -h' for help")