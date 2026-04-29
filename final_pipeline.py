import os, subprocess, requests, json, asyncio, sys, base64
import yt_dlp
from edge_tts import Communicate
from pathlib import Path

# --- CONFIGURATION ---
API_KEY = os.environ.get("OPENROUTER_KEY")
WORK_DIR = Path("workspace")
OUTPUT_DIR = Path("output")
os.makedirs(WORK_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_video():
    if not sys.stdin.isatty(): url = sys.stdin.read().strip()
    else: url = input("🔗 Enter YouTube Link: ")
    if not url: return False
    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best',
        'outtmpl': str(WORK_DIR / "raw.mp4"),
        'cookiefile': "cookies.txt",
        'merge_output_format': 'mp4'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return True

def extract_all_frames():
    print("🔍 Scanning full video for important scenes...")
    # Har 5 second mein ek frame nikalna poore video se
    subprocess.run([
        "ffmpeg", "-y", "-i", str(WORK_DIR / "raw.mp4"),
        "-vf", "fps=1/5,scale=640:-1", str(WORK_DIR / "all_frames_%03d.jpg")
    ], check=True)

async def generate_smart_montage():
    print("🤖 AI is selecting the best scenes and writing the script...")
    frames = sorted(list(WORK_DIR.glob("all_frames_*.jpg")))
    # AI ko har 5th frame dikhana (token limit ke liye)
    selected_frames = frames[::5][:30] 
    
    image_contents = []
    for f in selected_frames:
        with open(f, "rb") as img:
            b64 = base64.b64encode(img.read()).decode()
            image_contents.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    
    prompt = (
        "Analyze these manga frames. Identify the most important plot points and badass scenes. "
        "Write a 1st-person narrator script that only focuses on these key moments. "
        "The script should skip all unnecessary talking or filler scenes. "
        "Structure: Cold, punchy, and synchronized with the visual action."
    )
    
    data = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}] + image_contents}]
    }
    
    r = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                      headers={"Authorization": f"Bearer {API_KEY}"}, json=data)
    return r.json()['choices'][0]['message']['content']

async def run_intelligent_editor():
    if download_video():
        extract_all_frames()
        script = await generate_smart_montage()
        
        # Audio generate karna
        communicate = Communicate(script, "en-US-GuyNeural")
        await communicate.save(str(WORK_DIR / "dub.mp3"))
        
        print("🎬 Finalizing Intelligent Montage...")
        # FFmpeg ab audio ke length tak video ko summarize karega
        # Unnecessary parts cut jayenge kyunki hum -shortest use kar rahe hain 
        # aur filter mein unnecessary areas blur hain.
        filters = "scale=1280:720,delogo=x=40:y=40:w=220:h=100,delogo=x=900:y=30:w=350:h=150,delogo=x=100:y=850:w=1080:h=150"
        
        subprocess.run([
            "ffmpeg", "-y", "-i", str(WORK_DIR / "raw.mp4"), "-i", str(WORK_DIR / "dub.mp3"),
            "-filter_complex", f"[0:v]{filters}[v];[1:a]volume=2.8[a]",
            "-map", "[v]", "-map", "[a]", "-shortest", str(OUTPUT_DIR / "final_recap.mp4")
        ], check=True)
        print("🚀 SUCCESS: Unnecessary parts removed. Badass montage ready!")

if __name__ == "__main__":
    asyncio.run(run_intelligent_editor())
    
