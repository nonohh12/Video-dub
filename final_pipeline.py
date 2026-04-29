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
        url = input("🔗 Enter Win-XS YouTube Link: ")
        
    if not url: return False
    
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': f'{WORK_DIR}/raw.mp4',
        'overwrites': True,
        'cookiefile': COOKIE_FILE,
        'nocheckcertificate': True,
        # FIXED: String ki jagah list format use kiya hai
        'remote_components': ['ejs:github'], 
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'mweb'],
                # PO Token ke bina download karne ki koshish karne ke liye
                'skip': ['dash', 'hls'],
            }
        },
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }
    
    print(f"⏳ Downloading with fixed remote components...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        print(f"❌ Download Failed: {e}")
        return False

def clean_visuals():
    print("🧹 Removing Chinese text and watermarks...")
    # Win-XS channel optimized filters
    filters = (
        "delogo=x=40:y=40:w=220:h=100,"
        "delogo=x=800:y=30:w=260:h=140,"
        "delogo=x=50:y=860:w=980:h=140,"
        "delogo=x=150:y=550:w=300:h=150"
    )
    subprocess.run([
        "ffmpeg", "-y", "-i", f"{WORK_DIR}/raw.mp4",
        "-vf", filters, "-c:a", "copy", f"{WORK_DIR}/clean.mp4"
    ], check=True)

async def generate_revenge_script():
    print("🤖 Gemini 2.0 Flash (OpenRouter) is writing...")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    prompt = "Write a 1-minute dramatic English recap script about betrayal and revenge. MC returns with power. Badass energy."
    data = {"model": "google/gemini-2.0-flash-001", "messages": [{"role": "user", "content": prompt}]}
    try:
        r = requests.post(url, headers=headers, json=data)
        return r.json()['choices'][0]['message']['content']
    except:
        return "I was betrayed and left with nothing. But the system chose me. Now, the hunt begins."

async def make_dub(text):
    [span_0](start_span)print("🎙️ Edge-TTS Dubbing...") # Using Edge-TTS as per source[span_0](end_span)
    communicate = Communicate(text, "en-US-GuyNeural")
    await communicate.save(f"{WORK_DIR}/dub.mp3")

def merge_final():
    print("🎬 Final Merge...")
    cmd = (f"ffmpeg -y -i {WORK_DIR}/clean.mp4 -i {WORK_DIR}/dub.mp3 "
           f"{'-i ' + BGM_FILE if os.path.exists(BGM_FILE) else ''} "
           f"-filter_complex \"[1:a]volume=2.0[v];[2:a]volume=0.15[bg];[v][bg]amix=inputs=2:duration=first[a]\" "
           f"-map 0:v -map \"[a]\" -c:v libx264 -shortest {OUTPUT_DIR}/final_recap.mp4")
    if not os.path.exists(BGM_FILE):
        cmd = f"ffmpeg -y -i {WORK_DIR}/clean.mp4 -i {WORK_DIR}/dub.mp3 -c:v copy -map 0:v:0 -map 1:a:0 {OUTPUT_DIR}/final_recap.mp4"
    subprocess.run(cmd, shell=True, check=True)

async def run():
    if download_video():
        clean_visuals()
        script_text = await generate_revenge_script()
        await make_dub(script_text)
        merge_final()
        print("🚀 DONE!")

if __name__ == "__main__":
    asyncio.run(run())
    
