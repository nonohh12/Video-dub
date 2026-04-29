import os, subprocess, requests, json, asyncio, sys, base64
import yt_dlp
from edge_tts import Communicate
from pathlib import Path

# --- CONFIGURATION ---
API_KEY = os.environ.get("OPENROUTER_KEY")
WORK_DIR = Path("workspace")
OUTPUT_DIR = Path("output")
COOKIE_FILE = "cookies.txt"
BGM_FILE = "bgm.mp3"
os.makedirs(WORK_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_video():
    if not sys.stdin.isatty(): url = sys.stdin.read().strip()
    else: url = input("🔗 Enter YouTube Link: ")
    if not url: return False
    
    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best',
        'outtmpl': str(WORK_DIR / "raw.mp4"),
        'cookiefile': COOKIE_FILE,
        'merge_output_format': 'mp4',
        'remote_components': ['ejs:github'],
        'nocheckcertificate': True
    }
    print(f"⏳ Downloading video...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        print(f"❌ Download Failed: {e}")
        return False

async def generate_long_script():
    print("🤖 AI is analyzing and writing a LONG script...")
    # Extracting 20 frames for full context
    subprocess.run(["ffmpeg", "-y", "-i", str(WORK_DIR / "raw.mp4"), "-vf", "fps=1/60,scale=640:-1", str(WORK_DIR / "frame_%02d.jpg")], check=True)
    frames = sorted(list(WORK_DIR.glob("frame_*.jpg")))
    
    image_contents = []
    for f in frames[:20]:
        with open(f, "rb") as img:
            b64 = base64.b64encode(img.read()).decode()
            image_contents.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

    # STRICT PROMPT: No intros, only storytelling
    prompt = (
        "You are a professional Manga Narrator. Write a VERY LONG line-by-line explanation of this story. "
        "STRICT RULE: Do NOT say 'Here is the script' or 'Based on the frames'. "
        "START DIRECTLY with the story. Example: 'I was betrayed, left for dead...' "
        "Write at least 1500 words to cover the long video duration."
    )
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    data = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}] + image_contents}]
    }
    
    r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    response_text = r.json()['choices'][0]['message']['content']
    
    # Cleaning any accidental AI chat
    cleaned_script = response_text.replace("Here is the script:", "").replace("Narrator:", "").strip()
    return cleaned_script

async def run_final():
    if download_video():
        script = await generate_long_script()
        
        # Audio generation
        communicate = Communicate(script, "en-US-GuyNeural")
        await communicate.save(str(WORK_DIR / "dub.mp3"))
        
        print("🎬 Finalizing Render (No 0.7s cuts)...")
        # Filters: Scaling and cleaning Subtitles + Left/Right
        vf = "scale=1280:720,delogo=x=40:y=40:w=220:h=100,delogo=x=900:y=30:w=350:h=150,delogo=x=100:y=620:w=1080:h=100"
        
        # Audio Mixing: BGM loop logic added
        bgm_part = f"-stream_loop -1 -i {BGM_FILE}" if os.path.exists(BGM_FILE) else ""
        filter_complex = "[1:a]volume=2.8[v];[2:a]volume=0.10[bg];[v][bg]amix=inputs=2:duration=first[a]" if os.path.exists(BGM_FILE) else "[1:a]volume=2.5[a]"
        
        cmd = (
            f"ffmpeg -y -i {WORK_DIR}/raw.mp4 -i {WORK_DIR}/dub.mp3 {bgm_part} "
            f"-filter_complex \"[0:v]{vf}[outv];{filter_complex}\" "
            f"-map \"[outv]\" -map \"[a]\" -c:v libx264 -preset veryfast -shortest "
            f"{OUTPUT_DIR}/final_recap.mp4"
        )
        
        subprocess.run(cmd, shell=True, check=True)
        print("🚀 SUCCESS: Full length synced recap ready!")

if __name__ == "__main__":
    asyncio.run(run_final())
    
