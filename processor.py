import os, subprocess, requests, json, asyncio
import yt_dlp
from edge_tts import Communicate

# --- CONFIGURATION ---
API_KEY = os.environ.get("OPENROUTER_KEY")
WORK_DIR = "workspace"
OUTPUT_DIR = "output"
BGM_FILE = "bgm.mp3" # Make sure to upload your Suno AI BGM here

os.makedirs(WORK_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_video():
    url = input("🔗 Enter Win-XS YouTube Link: ")
    if not url: return False
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
        'outtmpl': f'{WORK_DIR}/raw.mp4',
        'overwrites': True
    }
    print("⏳ Downloading video...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return True

def clean_visuals():
    print("🧹 Removing Chinese text and watermarks...")
    # [span_1](start_span)Based on the screenshot you provided, cleaning 4 main zones[span_1](end_span)
    filters = (
        "delogo=x=40:y=40:w=220:h=100,"    # Top Left Status
        "delogo=x=800:y=30:w=260:h=140,"   # Top Right Disclaimer
        "delogo=x=50:y=860:w=980:h=140,"   # Bottom Subtitles Bar
        "delogo=x=150:y=550:w=300:h=150"   # Mid Left Stamp
    )
    subprocess.run([
        "ffmpeg", "-y", "-i", f"{WORK_DIR}/raw.mp4",
        "-vf", filters, "-c:a", "copy", f"{WORK_DIR}/clean.mp4"
    ], check=True)

async def generate_revenge_script():
    print("🤖 Gemini 2.0 Flash is writing the revenge story...")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    
    # Using the model you provided with high-energy "romanchak" prompt
    prompt = (
        "Write a 1-minute dramatic English recap script. "
        "Theme: Betrayal and cold revenge. The MC was humiliated but now he's back with a System. "
        "Use cold, badass, and exciting storytelling. No intro/outro."
    )
    
    data = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        r = requests.post(url, headers=headers, json=data)
        return r.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"❌ Script Error: {e}")
        return "He was betrayed, left for dead. But now, he has returned to take everything back."

async def make_dub(text):
    print("🎙️ Generating Edge-TTS 'Mast' Audio...")
    # [span_2](start_span)Using the exact model and voice from your provided script[span_2](end_span)
    communicate = Communicate(text, "en-US-GuyNeural")
    await communicate.save(f"{WORK_DIR}/dub.mp3")

def merge_final():
    print("🎬 Merging Clean Video + Dub + BGM...")
    if not os.path.exists(BGM_FILE):
        print("⚠️ Warning: bgm.mp3 not found. Merging without BGM.")
        cmd = f"ffmpeg -y -i {WORK_DIR}/clean.mp4 -i {WORK_DIR}/dub.mp3 -c:v copy -map 0:v:0 -map 1:a:0 {OUTPUT_DIR}/final_recap.mp4"
    else:
        # Merging with background music at 15% volume
        cmd = (
            f"ffmpeg -y -i {WORK_DIR}/clean.mp4 -i {WORK_DIR}/dub.mp3 -i {BGM_FILE} "
            f"-filter_complex \"[1:a]volume=2.0[v];[2:a]volume=0.15[bg];[v][bg]amix=inputs=2:duration=first[a]\" "
            f"-map 0:v -map \"[a]\" -c:v libx264 -preset fast -crf 22 {OUTPUT_DIR}/final_recap.mp4"
        )
    subprocess.run(cmd, shell=True, check=True)

async def run():
    if download_video():
        clean_visuals()
        script_text = await generate_revenge_script()
        await make_dub(script_text)
        merge_final()
        print(f"\n🚀 MISSION SUCCESSFUL! Check the '{OUTPUT_DIR}' folder.")

if __name__ == "__main__":
    asyncio.run(run())
    
