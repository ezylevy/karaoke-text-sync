# Karaoke Text Sync - Developer Procedure

## Overview
This system creates karaoke-style word highlighting synchronized with audio narration. Words are highlighted in real-time as they are spoken in the audio.

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Audio Files   │────▶│  AssemblyAI API  │────▶│   timings.js    │
│  (.mp3/.wav)    │     │  (transcription) │     │  (word timing)  │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│    Browser      │◀────│    index.html    │◀────│   syncData[]    │
│  (user sees)    │     │   (player UI)    │     │  [{start,end}]  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

---

## Step-by-Step Procedure

### Step 1: Prepare Your Files

Create a project folder with:
```
project/
├── audio_english.mp3    # English narration
├── audio_hebrew.mp3     # Hebrew narration (optional)
└── text.txt             # The text being narrated
```

**Requirements:**
- Audio files: MP3, WAV, or any web-compatible format
- Clear speech, minimal background noise for best results
- Text must match exactly what is spoken in the audio

---

### Step 2: Get AssemblyAI API Key

1. Go to https://www.assemblyai.com/
2. Sign up (free tier: 100 hours/month)
3. Copy your API key from the dashboard

---

### Step 3: Generate Word Timings

Create `sync_audio.py`:

```python
import requests
import time
import json

API_KEY = "YOUR_API_KEY_HERE"
BASE_URL = "https://api.assemblyai.com/v2"

def upload_audio(file_path):
    print(f"Uploading {file_path}...")
    with open(file_path, 'rb') as f:
        response = requests.post(
            f"{BASE_URL}/upload",
            headers={"Authorization": API_KEY},
            data=f
        )
    return response.json()['upload_url']

def transcribe(audio_url, language):
    print(f"Transcribing ({language})...")
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
    return response.json()['id']

def get_result(transcript_id):
    print("Processing", end="")
    while True:
        response = requests.get(
            f"{BASE_URL}/transcript/{transcript_id}",
            headers={"Authorization": API_KEY}
        )
        result = response.json()
        if result['status'] == 'completed':
            print(" Done!")
            return result
        elif result['status'] == 'error':
            raise Exception(result.get('error'))
        print(".", end="", flush=True)
        time.sleep(2)

def process_audio(file_path, language):
    upload_url = upload_audio(file_path)
    transcript_id = transcribe(upload_url, language)
    result = get_result(transcript_id)

    return [{
        "start": w['start'] / 1000,
        "end": w['end'] / 1000,
        "text": w['text']
    } for w in result.get('words', [])]

# Process your audio files
english_sync = process_audio("audio_english.mp3", "en")
hebrew_sync = process_audio("audio_hebrew.mp3", "he")

# Save to file
with open("timings.js", "w", encoding="utf-8") as f:
    f.write(f"const englishSyncData = {json.dumps(english_sync, indent=2, ensure_ascii=False)};\n\n")
    f.write(f"const hebrewSyncData = {json.dumps(hebrew_sync, indent=2, ensure_ascii=False)};\n")

print("Saved to timings.js!")
```

Run:
```bash
pip install requests
python sync_audio.py
```

---

### Step 4: Create the HTML Player

Create `index.html`:

```html
<!DOCTYPE html>
<html lang="he">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Karaoke Text Sync</title>
    <style>
        .transcript {
            font-size: 1.6em;
            line-height: 2.2;
            padding: 15px;
        }
        .transcript span {
            padding: 4px 6px;
            margin: 2px;
            border-radius: 4px;
            transition: all 0.1s;
            display: inline-block;
        }
        .transcript span.active {
            background: linear-gradient(135deg, #ffeb3b, #ffc107);
            transform: scale(1.1);
            box-shadow: 0 2px 8px rgba(255,193,7,0.4);
        }
        /* For RTL languages like Hebrew */
        .hebrew { direction: rtl; text-align: right; }
    </style>
</head>
<body>
    <div class="transcript" id="transcript"></div>
    <audio id="audio" src="audio.mp3" controls></audio>
    <button id="toggle">Disable Highlight</button>

    <script>
        // Paste your syncData here (from timings.js)
        const syncData = [
            { start: 0.16, end: 0.44, text: "Word1" },
            { start: 0.44, end: 0.84, text: "Word2" },
            // ... more words
        ];

        const audio = document.getElementById('audio');
        const transcript = document.getElementById('transcript');
        let karaokeOn = true;
        let spans = [];

        // Build transcript
        syncData.forEach(item => {
            const span = document.createElement('span');
            span.textContent = item.text;
            span.dataset.start = item.start;
            span.dataset.end = item.end;
            transcript.appendChild(span);
            transcript.appendChild(document.createTextNode(' '));
            spans.push(span);
        });

        // Sync highlighting with audio
        audio.addEventListener('timeupdate', () => {
            if (!karaokeOn) return;
            const t = audio.currentTime;
            spans.forEach(span => {
                const s = parseFloat(span.dataset.start);
                const e = parseFloat(span.dataset.end);
                span.classList.toggle('active', t >= s && t < e);
            });
        });

        // Toggle button
        document.getElementById('toggle').addEventListener('click', function() {
            karaokeOn = !karaokeOn;
            this.textContent = karaokeOn ? 'Disable Highlight' : 'Enable Highlight';
            if (!karaokeOn) spans.forEach(span => span.classList.remove('active'));
        });
    </script>
</body>
</html>
```

---

### Step 5: Verify and Fix Transcription Errors

The API may make transcription mistakes. Review `timings.js` and fix any errors:

```javascript
// WRONG (API mistake)
{ start: 1.131, end: 1.511, text: "ליטום" }

// CORRECT (manual fix)
{ start: 1.131, end: 1.511, text: "לטעום" }
```

**Keep the timing values - only fix the text!**

---

## Data Structure Reference

### syncData Format
```javascript
const syncData = [
    {
        start: 0.16,    // Start time in seconds
        end: 0.44,      // End time in seconds
        text: "Word"    // The word to display
    },
    // ... more words
];
```

### AssemblyAI Response
```javascript
{
    words: [
        {
            start: 160,     // Start time in milliseconds
            end: 440,       // End time in milliseconds
            text: "Word",
            confidence: 0.99
        }
    ]
}
```

**Note:** AssemblyAI returns milliseconds, divide by 1000 for seconds.

---

## Supported Languages

AssemblyAI supports:
- `en` - English
- `he` - Hebrew
- `es` - Spanish
- `fr` - French
- `de` - German
- `ar` - Arabic
- And many more...

Full list: https://www.assemblyai.com/docs/concepts/supported-languages

---

## Troubleshooting

### Problem: Words highlight at wrong time
**Solution:** The transcription timing may be slightly off. Manually adjust start/end times by ±0.1 seconds.

### Problem: API returns "speech_models" error
**Solution:** Use `"speech_models": ["universal-2"]` in the request.

### Problem: Hebrew text displays incorrectly
**Solution:** Add `direction: rtl` CSS and ensure UTF-8 encoding.

### Problem: Audio doesn't play
**Solution:** Ensure audio file is in the same folder and format is supported (MP3, WAV, OGG).

---

## File Structure (Final)

```
project/
├── index.html          # Main player page
├── audio_english.mp3   # English audio
├── audio_hebrew.mp3    # Hebrew audio
├── timings.js          # Generated word timings
├── sync_audio.py       # Script to generate timings
└── PROCEDURE.md        # This document
```

---

## Quick Reference

| Task | Command/Action |
|------|----------------|
| Install dependencies | `pip install requests` |
| Generate timings | `python sync_audio.py` |
| Test locally | Open `index.html` in browser |
| Deploy | Upload to GitHub Pages or any web host |

---

## API Costs

AssemblyAI Pricing:
- **Free tier:** 100 hours/month
- **Pay-as-you-go:** ~$0.37/hour after free tier

For a typical short audio (30 seconds), cost is negligible.

---

## Contact

Repository: https://github.com/ezylevy/karaoke-text-sync
