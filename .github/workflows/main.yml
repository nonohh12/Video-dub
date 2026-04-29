import os, subprocess, requests, json, asyncio, sys
import yt_dlp
from edge_tts import Communicate

# --- CONFIGURATION ---
API_KEY = os.environ.get("OPENROUTER_KEY")
WORK_DIR = "workspace"
OUTPUT_DIR = "output"
BGM_FILE = "bgm.mp3" 
COOKIE_FILE = "cookies.txt"

os.makedirs(WORK_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_video():
    if not sys.stdin.isatty():
        url = sys.stdin.read().strip()
    else:
        url = input("🔗 Enter YouTube Link: ")
    if not url: return False
    
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': f'{WORK_DIR}/raw.mp4',
        'overwrites': True,
        'cookiefile': COOKIE_FILE,
        'merge_output_format': 'mp4',
        'remote_components': ['ejs:github'],
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        print(f"❌ Download Failed: {e}")
        return False

def clean_visuals():
    print("🧹 Cleaning watermarks and scaling (2 min segment)...")
    # -t 120 means only first 2 minutes will be processed
    filters = (
        "scale=1280:720,"
        "delogo=x=40:y=40:w=220:h=100,"    
        "delogo=x=900:y=30:w=260:h=140,"   
        "delogo=x=150:y=580:w=980:h=130,"  
        "delogo=x=150:y=400:w=250:h=120"   
    )
    subprocess.run(["ffmpeg", "-y", "-t", "120", "-i", f"{WORK_DIR}/raw.mp4", "-vf", filters, "-c:a", "copy", f"{WORK_DIR}/clean.mp4"], check=True)

async def generate_narrator_script():
    print("🤖 Gemini 2.0 Flash is creating line-by-line explanation...")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    
    # [span_3](start_span)Narrator 'I/Me' perspective prompt[span_3](end_span)
    prompt = (
        "Write a 2-minute line-by-line manga explanation script in first-person perspective. "
        "Example style: 'They thought I was weak, so I showed them my system. I took the blade and...' "
        "Theme: Betrayal and cold revenge. Make it badass and punchy. No intro."
    )
    
    data = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        r = requests.post(url, headers=headers, json=data)
        return r.json()['choices'][0]['message']['content']
    except:
        return "I stood there, watching them laugh at my misery. Little did they know, my revenge had already begun."

async def make_dub(text):
    print("🎙️ Generating Narrator Voice (Edge-TTS)...") #
    communicate = Communicate(text, "en-US-GuyNeural")
    await communicate.save(f"{WORK_DIR}/dub.mp3")

def merge_final():
    print("🎬 Merging 2-minute Recap...")
    # Dub volume 2.5x and BGM volume 0.12x for that pro feel
    cmd = (f"ffmpeg -y -i {WORK_DIR}/clean.mp4 -i {WORK_DIR}/dub.mp3 "
           f"{'-i ' + BGM_FILE if os.path.exists(BGM_FILE) else ''} "
           f"-filter_complex \"[1:a]volume=2.5[v];[2:a]volume=0.12[bg];[v][bg]amix=inputs=2:duration=first[a]\" "
           f"-map 0:v -map \"[a]\" -c:v libx264 -shortest {OUTPUT_DIR}/final_recap.mp4")
    if not os.path.exists(BGM_FILE):
        cmd = f"ffmpeg -y -i {WORK_DIR}/clean.mp4 -i {WORK_DIR}/dub.mp3 -c:v copy -map 0:v:0 -map 1:a:0 {OUTPUT_DIR}/final_recap.mp4"
    subprocess.run(cmd, shell=True, check=True)

async def run():
    if download_video():
        clean_visuals()
        script_text = await generate_narrator_script()
        await make_dub(script_text)
        merge_final()
        print("🚀 2-MIN NARRATOR RECAP DONE!")

if __name__ == "__main__":
    asyncio.run(run())
    
