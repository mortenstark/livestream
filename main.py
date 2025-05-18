import asyncio
import time
from voicemeeter import VoicemeeterRemote
from browser import launch_browser_with_auth
from audio_capture import record_audio_from_output

def print_with_timestamp(message, last_time=None):
    """Print a message with a timestamp and time since the last message."""
    current_time = time.time()
    timestamp = time.strftime("%H:%M:%S", time.localtime(current_time))
    elapsed = f"(+{current_time - last_time:.2f}s)" if last_time else ""
    print(f"{timestamp} {elapsed} {message}")
    return current_time

async def main(debug=False):
    last_time = None

    # Initialize Voicemeeter
    vm = VoicemeeterRemote()
    vm.login()

    # Configure Voicemeeter routing
    last_time = print_with_timestamp("Configuring Voicemeeter routing...", last_time)
    vm.configure_routing(debug=debug)

    try:
        # Launch browser with authentication
        last_time = print_with_timestamp("Launching browser with authentication...", last_time)
        await launch_browser_with_auth()

        # Record audio from NotebookLM
        last_time = print_with_timestamp("Starting audio recording...", last_time)
        record_audio_from_output(output_device_name="CABLE Output (VB-Audio Virtual Cable)", duration=60)
        last_time = print_with_timestamp("Audio recording completed.", last_time)
    except KeyboardInterrupt:
        print_with_timestamp("Program terminated by user", last_time)
    except Exception as e:
        print_with_timestamp(f"Error: {e}", last_time)
    finally:
        # Clean up Voicemeeter
        last_time = print_with_timestamp("Cleaning up Voicemeeter...", last_time)
        vm.logout()

if __name__ == "__main__":
    asyncio.run(main(debug=False))  # Set debug=True for detailed output