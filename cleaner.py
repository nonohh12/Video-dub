import subprocess

def clean_video():
    # Aapne jo areas highlight kiye unke coordinates (x:y:w:h)
    # Ye coordinates Win-XS ke standard videos ke hisaab se adjust kiye hain
    filters = [
        "delogo=x=40:y=40:w=220:h=120",    # Top Left (Status)
        "delogo=x=800:y=40:w=250:h=150",   # Top Right (Disclaimer)
        "delogo=x=150:y=550:w=300:h=150",  # Mid Left Stamp
        "delogo=x=50:y=850:w=980:h=150"    # Bottom Subtitles bar
    ]
    
    vf_string = ",".join(filters)
    
    cmd = [
        "ffmpeg", "-y", "-i", "workspace/raw_video.mp4",
        "-vf", vf_string,
        "-c:a", "copy", "workspace/clean_video.mp4"
    ]
    subprocess.run(cmd)
    print("✅ Watermarks blurred.")

if __name__ == "__main__":
    clean_video()
  
