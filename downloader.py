import yt_dlp
import os

def download_video():
    url = input("Enter YouTube video URL: ")
    if not url: 
        print("No URL provided. Skipping...")
        return
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'workspace/raw_video.mp4',
        'overwrites': True,
    }
    
    if os.path.exists('workspace/raw_video.mp4'):
        print("Video already exists, skipping download.")
    else:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("✅ Download complete.")

if __name__ == "__main__":
    os.makedirs("workspace", exist_ok=True)
    download_video()
  
