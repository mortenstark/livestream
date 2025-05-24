# Audio Injection Setup Guide for NotebookML

This guide explains how to set up and use the audio injection solution for NotebookML using VB-Cable.

## Prerequisites

1. **VB-Cable Installation**
   - Download and install [VB-Cable](https://vb-audio.com/Cable/) from the official website
   - This creates two virtual audio devices:
     - CABLE Input (virtual microphone)
     - CABLE Output (virtual speaker)

2. **Python Dependencies**
   ```bash
   pip install sounddevice soundfile numpy playwright
   ```

## Setup Steps

### 1. Find Your Audio Device Indices

Run the following command to list all audio devices and find the indices for VB-Cable devices:

```bash
python -c "from audio import list_audio_devices; list_audio_devices()"
```

Look for:
- CABLE Input (VB-Audio Virtual Cable) - Note its device index (e.g., 87)
- CABLE Output (VB-Audio Virtual Cable) - Note its device index

### 2. Update Configuration

Edit `config.py` to set the correct device index:

```python
# Audio device configuration
TTS_OUTPUT_DEVICE = "CABLE Input"  # VB-Cable input device (sends audio)
AUDIO_INPUT_DEVICE = "CABLE Output"  # VB-Cable output device (receives audio)
AUDIO_DEVICE_INDEX = 87  # Replace with your CABLE Input device index
DEFAULT_GAIN = 3.0  # Adjust if needed for proper volume
```

### 3. Test Audio Playback

Test that audio playback works correctly:

```bash
python -c "from audio import play_audio_file; play_audio_file(monitor=True, debug=True)"
```

You should see level monitoring and hear the audio through the VB-Cable.

### 4. Run the Application

Start the application:

```bash
python main.py
```

The application will:
1. Check for VB-Cable devices
2. Launch Chrome/Chromium
3. Navigate to NotebookML
4. Set up the Dr. Farsight Podcast in Interactive Mode
5. Prompt you to configure Chrome to use CABLE Output as the microphone
6. Play the TTS file through CABLE Input when the podcast is in listening mode
7. Record the response from the podcast

## Troubleshooting

### No Sound in NotebookML

1. **Verify Chrome is using the correct microphone**
   - In Chrome, go to Settings > Privacy and security > Site Settings > Microphone
   - Select "CABLE Output (VB-Audio Virtual Cable)" for notebooklm.google.com

2. **Check device indices**
   - Run the list_audio_devices() function to verify the indices
   - Update AUDIO_DEVICE_INDEX in config.py if needed

3. **Adjust gain**
   - If the volume is too low, increase DEFAULT_GAIN in config.py (try 4.0 or 5.0)

### Distorted Audio

1. **Reduce gain**
   - If audio is distorted, decrease DEFAULT_GAIN in config.py (try 2.0 or 1.5)

2. **Check for clipping**
   - Use the monitor=True parameter to see audio levels
   - Levels consistently at maximum indicate clipping

### Browser Issues

1. **Authentication problems**
   - Delete auth.json and let the application create a new one

2. **Selector errors**
   - The application may fail if NotebookML's UI changes
   - Check error_screenshot.png for debugging

## Advanced Usage

### Command-line Tools

The updated code includes several command-line tools:

1. **List audio devices**
   ```bash
   python audio.py list
   ```

2. **Play audio with monitoring**
   ```bash
   python audio.py play graham.wav --monitor --gain 3.0
   ```

3. **Generate test tone**
   ```bash
   python audio.py tone --freq 440 --duration 3 --gain 2.0
   ```

4. **Record audio**
   ```bash
   python audio_capture.py record --duration 10 --monitor
   ```

5. **Play and record**
   ```bash
   python audio_capture.py playrecord graham.wav --duration 10 --monitor
   ```
