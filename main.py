#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import asyncio
import argparse
from datetime import datetime
import traceback
import platform

from browser import launch_browser_with_auth
from audio import list_audio_devices
from config import RECORDING_DIR

def kill_all_chromium():
    """Dræber alle kørende Chromium-processer for at sikre en ren start"""
    import os
    import platform

    system = platform.system()

    try:
        if system == "Windows":
            os.system("taskkill /f /im chromium.exe >nul 2>&1")
            print("✅ Alle Chromium-processer afsluttet (Windows)")
        elif system == "Darwin":  # macOS
            os.system("pkill -f 'Chromium' >/dev/null 2>&1")
            print("✅ Alle Chromium-processer afsluttet (macOS)")
        elif system == "Linux":
            os.system("pkill -f chromium >/dev/null 2>&1")
            print("✅ Alle Chromium-processer afsluttet (Linux)")
        else:
            print(f"⚠️ Ukendt operativsystem: {system}, kan ikke afslutte Chromium-processer")
    except Exception as e:
        print(f"⚠️ Fejl ved afslutning af Chromium-processer: {e}")

async def main(debug_mode=False, tts_file=None):
    """Hovedfunktion der kører hele processen"""
    try:
        # Sørg for at output-mappen eksisterer
        os.makedirs(RECORDING_DIR, exist_ok=True)
        
        # Opdater TTS_FILE_PATH i config hvis specificeret
        if tts_file:
            from config import TTS_FILE_PATH
            # Gem den oprindelige værdi
            original_tts_path = TTS_FILE_PATH
            # Opdater config-modulet dynamisk
            import config
            config.TTS_FILE_PATH = tts_file
            if debug_mode:
                print(f"DEBUG: Using custom TTS file: {tts_file}")
                print(f"DEBUG: Original TTS file was: {original_tts_path}")
        
        # Start browser og kør interaktionen
        await launch_browser_with_auth(debug_mode=debug_mode)
        
    except Exception as e:
        if debug_mode:
            print(f"DEBUG: Error in main function: {e}")
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
        else:
            print(f"Error in main function: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="NotebookLM Podcast Automation")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--tts", type=str, help="Path to TTS audio file to use")
    args = parser.parse_args()

    # Kill all Chromium processes before starting
    kill_all_chromium()

    # Run the main function
    exit_code = asyncio.run(main(debug_mode=args.debug, tts_file=args.tts))
    sys.exit(exit_code)