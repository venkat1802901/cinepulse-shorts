import subprocess
import time
import sys
import os
import re

BASE_DIR = r"C:\Users\venkat\.gemini\antigravity\scratch\viral_shorts_production"
SERVER_SCRIPT = os.path.join(BASE_DIR, "app", "server.py")
CLOUDFLARED = os.path.join(BASE_DIR, "cloudflared.exe")
TUNNEL_FILE = os.path.join(BASE_DIR, "app", "data", "tunnel_url.txt")

def start_services():
    print("Starting CinePulse Flask Server...")
    flask_proc = subprocess.Popen([sys.executable, SERVER_SCRIPT])
    time.sleep(2)

    print("Starting Cloudflare Tunnel...")
    cf_proc = subprocess.Popen(
        [CLOUDFLARED, "tunnel", "--url", "http://127.0.0.1:5050"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    tunnel_url = None
    for line in cf_proc.stdout:
        print(line, end="")
        match = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
        if match:
            tunnel_url = match.group(0)
            print(f"\n=======================================================")
            print(f"🔥 CINEPULSE MOBILE APP URL: {tunnel_url}")
            print(f"=======================================================\n")
            with open(TUNNEL_FILE, "w", encoding="utf-8") as f:
                f.write(tunnel_url)
            break

    try:
        while True:
            time.sleep(1)
            if flask_proc.poll() is not None:
                print("Flask server stopped, restarting...")
                flask_proc = subprocess.Popen([sys.executable, SERVER_SCRIPT])
            if cf_proc.poll() is not None:
                print("Cloudflared tunnel stopped, restarting...")
                cf_proc = subprocess.Popen(
                    [CLOUDFLARED, "tunnel", "--url", "http://127.0.0.1:5050"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
    except KeyboardInterrupt:
        flask_proc.terminate()
        cf_proc.terminate()

if __name__ == '__main__':
    start_services()
