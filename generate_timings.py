"""
Generate word-level timings from audio files using AssemblyAI API.
Outputs syncData that can be used in the HTML karaoke player.

Usage:
1. Get a free API key from https://www.assemblyai.com/ (100 hours/month free)
2. Install: pip install assemblyai
3. Run: python generate_timings.py

The script will create a 'timings.js' file with the sync data.
"""

import assemblyai as aai
import json
import os

# ============ CONFIGURATION ============
# Get your free API key from: https://www.assemblyai.com/
API_KEY = "YOUR_API_KEY_HERE"  # Replace with your API key

# Audio files to process
AUDIO_FILES = {
    "english": {
        "file": "Cat.mp3",
        "language": "en"
    },
    "hebrew": {
        "file": "Cat_HE.mp3",
        "language": "he"
    }
}

# ============ MAIN CODE ============
def transcribe_audio(file_path, language_code):
    """Transcribe audio and get word-level timestamps."""

    print(f"Transcribing: {file_path} (language: {language_code})")

    # Configure AssemblyAI
    aai.settings.api_key = API_KEY

    # Configure transcription
    config = aai.TranscriptionConfig(
        language_code=language_code,
        punctuate=True,
        format_text=False
    )

    # Create transcriber and transcribe
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(file_path, config=config)

    if transcript.status == aai.TranscriptStatus.error:
        print(f"Error: {transcript.error}")
        return None

    # Extract word timings
    sync_data = []
    for word in transcript.words:
        sync_data.append({
            "start": word.start / 1000,  # Convert ms to seconds
            "end": word.end / 1000,
            "text": word.text
        })

    print(f"  Found {len(sync_data)} words")
    return sync_data


def main():
    if API_KEY == "YOUR_API_KEY_HERE":
        print("=" * 50)
        print("ERROR: Please set your AssemblyAI API key!")
        print("")
        print("1. Go to https://www.assemblyai.com/")
        print("2. Sign up for free (100 hours/month)")
        print("3. Copy your API key")
        print("4. Replace 'YOUR_API_KEY_HERE' in this script")
        print("=" * 50)
        return

    results = {}

    for name, config in AUDIO_FILES.items():
        file_path = config["file"]

        if not os.path.exists(file_path):
            print(f"Warning: {file_path} not found, skipping...")
            continue

        sync_data = transcribe_audio(file_path, config["language"])
        if sync_data:
            results[name] = sync_data

    if not results:
        print("No files were processed.")
        return

    # Generate JavaScript file
    js_content = "// Auto-generated word timings from AssemblyAI\n"
    js_content += "// Generated on: " + __import__('datetime').datetime.now().isoformat() + "\n\n"

    for name, sync_data in results.items():
        var_name = f"{name}SyncData"
        js_content += f"const {var_name} = {json.dumps(sync_data, indent=2, ensure_ascii=False)};\n\n"

    # Save to file
    with open("timings.js", "w", encoding="utf-8") as f:
        f.write(js_content)

    print("\n" + "=" * 50)
    print("SUCCESS! Timings saved to 'timings.js'")
    print("=" * 50)

    # Also print for easy copy-paste
    print("\nYou can copy these directly into your HTML:\n")
    print(js_content)


if __name__ == "__main__":
    main()
