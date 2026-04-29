import os, subprocess, requests, json, time
import yt_dlp
from edge_tts import Communicate
import asyncio

# Configuration
API_KEY = os.environ.get("OPENROUTER_KEY")
WORK_DIR = "workspace"
OUTPUT_DIR = "output"
os.makedirs(WORK_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_yt():
    url = input("Enter YouTube Video Link: ")
    if not url: return False
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
        'outtmpl': f'{WORK_DIR}/raw.mp4',
        'overwrites': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return True

def clean_watermarks():
    print("🧹 Cleaning watermarks and Chinese text...")
    # Win-XS channel ke typical watermark locations
    filters = (
        "delogo=x=40:y=40:w=220:h=100,"    # Top Left
        "delogo=x=800:y=30:w=260:h=140,"   # Top Right
        "delogo=x=50:y=860:w=980:h=140"    # Bottom Subtitles
    )
    subprocess.run([
        "ffmpeg", "-y", "-i", f"{WORK_DIR}/raw.mp4",
        "-vf", filters, "-c:a", "copy", f"{WORK_DIR}/clean.mp4"
    ], check=True)

def get_gemini_script():
    print("🤖 Generating dramatic revenge script via Gemini...")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    
    [span_2](start_span)# Gemini 2.0 Flash usage
    prompt = "Create a cold, dramatic 1-minute English narration for a manga recap. Theme: Betrayal and ultimate revenge. No intro, just the story."
    
    data = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    r = requests.post(url, headers=headers, json=data)
    return r.json()['choices'][0]['message']['content']

async def make_dub(text):
    print("🎙️ Generating Edge-TTS Dubbing...")
    # Using Edge-TTS as per your provided files
    communicate = Communicate(text, "en-US-GuyNeural")
    await communicate.save(f"{WORK_DIR}/dub.mp3")

def final_merge():
    print("🎞️ Merging Video, Dub, and BGM...")
    # Note: Make sure 'bgm.mp3' is in your folder
    cmd = [
        "ffmpeg", "-y", "-i", f"{WORK_DIR}/clean.mp4", 
        "-i", f"{WORK_DIR}/dub.mp3", 
        "-i", "bgm.mp3",
        "-filter_complex", "[1:a]volume=1.8[vocal];[2:a]volume=0.15[bg];[vocal][bg]amix=inputs=2:duration=first[a]",
        "-map 0:v", "-map [a]", "-c:v libx264", "-shortest", f"{OUTPUT_DIR}/final_recap.mp4"
    ]
    subprocess.run(" ".join(cmd), shell=True, check=True)

async def main():
    if download_yt():
        clean_watermarks()
        script = get_gemini_script()
        await make_dub(script)
        final_merge()
        print(f"🚀 DONE! Video saved in {OUTPUT_DIR}")

if __name__ == "__main__":
    asyncio.run(main())
