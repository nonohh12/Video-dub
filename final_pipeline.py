import os, subprocess, requests, json, asyncio, sys, base64
import yt_dlp
from edge_tts import Communicate
from pathlib import Path

# --- CONFIGURATION ---
API_KEY = os.environ.get("OPENROUTER_KEY")
WORK_DIR = Path("workspace")
OUTPUT_DIR = Path("output")
COOKIE_FILE = "cookies.txt"
os.makedirs(WORK_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_video():
    if not sys.stdin.isatty(): url = sys.stdin.read().strip()
    else: url = input("🔗 Enter YouTube Link: ")
    if not url: return False
    
    ydl_opts = {
        # FIXED: Format ko more flexible rakha hai taki error na aaye
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': str(WORK_DIR / "raw.mp4"),
        'cookiefile': COOKIE_FILE,
        'merge_output_format': 'mp4',
        'remote_components': ['ejs:github'], # Required for JS challenges
        'nocheckcertificate': True,
        'extractor_args': {'youtube': {'player_client': ['web', 'mweb']}}
    }
    print(f"⏳ Downloading video (Attempting bypass)...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        print(f"❌ Download Failed: {e}")
        return False

def extract_all_frames():
    print("🔍 Scanning full video to identify key moments...")
    # Har 10 second mein ek frame (17 min video = ~100 frames)
    subprocess.run([
        "ffmpeg", "-y", "-i", str(WORK_DIR / "raw.mp4"),
        "-vf", "fps=1/10,scale=640:-1", str(WORK_DIR / "all_frames_%03d.jpg")
    ], check=True)

async def generate_smart_montage():
    print("🤖 AI is reading frames to eliminate unnecessary scenes...")
    frames = sorted(list(WORK_DIR.glob("all_frames_*.jpg")))
    # Token limit ke liye key frames select karna (First, middle, last sequence)
    selected_frames = frames[::10][:25] 
    
    image_contents = []
    for f in selected_frames:
        with open(f, "rb") as img:
            b64 = base64.b64encode(img.read()).decode()
            image_contents.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    
    prompt = (
        "You are an expert Manga Editor. Analyze these frames. "
        "Write a 1st-person 'I/Me' narrator script that only covers the most badass and important plot points. "
        "Ignore all filler and unnecessary scenes. Each sentence must perfectly match the visual flow. "
        "Make it cold, dramatic, and punchy."
    )
    
    data = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}] + image_contents}]
    }
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    return r.json()['choices'][0]['message']['content']

async def run_intelligent_editor():
    if download_video():
        extract_all_frames()
        script = await generate_smart_montage()
        
        # Audio generation
        communicate = Communicate(script, "en-US-GuyNeural")
        await communicate.save(str(WORK_DIR / "dub.mp3"))
        
        print("🎬 Finalizing Intelligent Montage (Cutting unnecessary parts)...")
        # Filters to clean watermarks (Left, Right, Subtitles only)
        filters = (
            "scale=1280:720,"
            "delogo=x=40:y=40:w=220:h=100,"    # Top Left
            "delogo=x=900:y=30:w=350:h=150,"   # Top Right
            "delogo=x=150:y=600:w=980:h=110"   # Subtitles Area
        )
        
        # -shortest will automatically cut the video when the AI script ends
        subprocess.run([
            "ffmpeg", "-y", "-i", str(WORK_DIR / "raw.mp4"), "-i", str(WORK_DIR / "dub.mp3"),
            "-filter_complex", f"[0:v]{filters}[v];[1:a]volume=2.8[a]",
            "-map", "[v]", "-map", "[a]", "-shortest", str(OUTPUT_DIR / "final_recap.mp4")
        ], check=True)
        print("🚀 SUCCESS: Badass intelligent recap is ready!")

if __name__ == "__main__":
    asyncio.run(run_intelligent_editor())
    
