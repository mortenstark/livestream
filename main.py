import asyncio
from voicemeeter import VoicemeeterRemote
from browser import launch_browser_with_auth

async def main():
    # Initialize Voicemeeter
    vm = VoicemeeterRemote()
    vm.login()

    # Configure Voicemeeter routing
    vm.configure_routing()

    try:
        # Launch browser with authentication
        await launch_browser_with_auth()
    except KeyboardInterrupt:
        print("Program terminated by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up Voicemeeter
        vm.logout()

if __name__ == "__main__":
    asyncio.run(main())