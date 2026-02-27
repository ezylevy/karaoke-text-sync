import requests
import time
import json

API_KEY = "YOUR_API_KEY_HERE"  # Get free key from assemblyai.com
BASE_URL = "https://api.assemblyai.com/v2"

def upload_audio(file_path):
    """Upload audio file to AssemblyAI"""
    print(f"Uploading {file_path}...")

    with open(file_path, 'rb') as f:
        response = requests.post(
            f"{BASE_URL}/upload",
            headers={"Authorization": API_KEY},
            data=f
        )

    if response.status_code != 200:
        print(f"Upload error: {response.text}")
        return None

    return response.json()['upload_url']

def transcribe(audio_url, language):
    """Request transcription"""
    print(f"Requesting transcription ({language})...")

    response = requests.post(
        f"{BASE_URL}/transcript",
        headers={
            "Authorization": API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "audio_url": audio_url,
            "language_code": language,
            "speech_models": ["universal-2"]
        }
    )

    if response.status_code != 200:
        print(f"Transcription error: {response.text}")
        return None

    return response.json()['id']

def get_result(transcript_id):
    """Poll for transcription result"""
    print("Processing", end="")

    while True:
        response = requests.get(
            f"{BASE_URL}/transcript/{transcript_id}",
            headers={"Authorization": API_KEY}
        )

        result = response.json()
        status = result['status']

        if status == 'completed':
            print(" Done!")
            return result
        elif status == 'error':
            print(f" Error: {result.get('error', 'Unknown error')}")
            return None

        print(".", end="", flush=True)
        time.sleep(2)

def process_audio(file_path, language):
    """Full pipeline: upload, transcribe, get results"""

    # Upload
    upload_url = upload_audio(file_path)
    if not upload_url:
        return None

    # Transcribe
    transcript_id = transcribe(upload_url, language)
    if not transcript_id:
        return None

    # Get result
    result = get_result(transcript_id)
    if not result:
        return None

    # Extract word timings
    words = result.get('words', [])
    sync_data = []

    for w in words:
        sync_data.append({
            "start": w['start'] / 1000,
            "end": w['end'] / 1000,
            "text": w['text']
        })

    return sync_data

def main():
    print("=" * 50)
    print("AssemblyAI Word Timing Generator")
    print("=" * 50)

    # Process English
    print("\n[English Audio]")
    en_sync = process_audio("Cat.mp3", "en")

    # Process Hebrew
    print("\n[Hebrew Audio]")
    he_sync = process_audio("Cat_HE.mp3", "he")

    # Generate timings.js
    print("\n" + "=" * 50)
    print("Generating timings.js...")

    js_content = "// Auto-generated word timings from AssemblyAI\n\n"

    if en_sync:
        js_content += f"const englishSyncData = {json.dumps(en_sync, indent=2, ensure_ascii=False)};\n\n"
        print(f"English: {len(en_sync)} words")

    if he_sync:
        js_content += f"const hebrewSyncData = {json.dumps(he_sync, indent=2, ensure_ascii=False)};\n\n"
        print(f"Hebrew: {len(he_sync)} words")

    with open("timings.js", "w", encoding="utf-8") as f:
        f.write(js_content)

    print("\nSaved to timings.js!")
    print("=" * 50)

if __name__ == "__main__":
    main()
