# -*- coding: utf-8 -*-
"""
Roadside Assistance - Django + Cloudflare Tunnel Launcher
Uses trycloudflare.com for public HTTPS access
"""
import subprocess
import sys
import os
import signal
import time
import re

def print_banner():
    print("""
===============================================
Roadside Assistance - Django + Cloudflare
===============================================

This script will:
  1. Start Django development server on port 8000
  2. Start Cloudflare tunnel (trycloudflare.com)

Use the Cloudflare URL with PWA Builder
Press Ctrl+C to stop both servers
===============================================
""")

def start_django():
    """Start Django development server"""
    print("[INFO] Starting Django server on port 8000...")
    django_process = subprocess.Popen(
        [sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000'],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    return django_process

def start_cloudflare():
    """Start Cloudflare tunnel"""
    print("[INFO] Starting Cloudflare tunnel...")

    # Find cloudflared executable
    cloudflared_path = None
    possible_paths = [
        r'C:\Users\sid\AppData\Roaming\npm\cloudflared.cmd',
        r'C:\Users\sid\AppData\Roaming\npm\cloudflared',
        'cloudflared',
        'cloudflared.exe'
    ]

    for path in possible_paths:
        if os.path.exists(path) or path == 'cloudflared':
            cloudflared_path = path
            break

    if not cloudflared_path:
        # Try shell=True for command lookup
        cloudflared_cmd = 'cloudflared tunnel --url http://localhost:8000'
        cloudflare_process = subprocess.Popen(
            cloudflared_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True
        )
    else:
        cloudflare_process = subprocess.Popen(
            [cloudflared_path, 'tunnel', '--url', 'http://localhost:8000'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

    return cloudflare_process

def extract_cloudflare_url(cloudflare_process):
    """Extract the Cloudflare tunnel URL from output"""
    print("[INFO] Waiting for Cloudflare URL...")

    url_found = False
    for line in iter(cloudflare_process.stdout.readline, ''):
        print(line.rstrip())

        # Look for the trycloudflare.com URL
        if 'trycloudflare.com' in line:
            match = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
            if match:
                url = match.group(0)
                if not url_found:
                    url_found = True
                    print("\n" + "="*60)
                    print("  YOUR APP IS LIVE AT:")
                    print(f"  {url}")
                    print("="*60)
                    print("\nUse this URL with:")
                    print("  - PWA Builder: https://pwabuilder.com")
                    print("  - Direct browser access for testing\n")

                    # Save to file
                    with open('cloudflare_url.txt', 'w') as f:
                        f.write(url)
                    print(f"[INFO] URL saved to cloudflare_url.txt\n")

    return None

def main():
    print_banner()

    processes = []

    try:
        # Start Django
        django_process = start_django()
        processes.append(('Django', django_process))
        print("[OK] Django server started")

        # Start Cloudflare
        cloudflare_process = start_cloudflare()
        processes.append(('Cloudflare', cloudflare_process))

        # Extract and display URL
        extract_cloudflare_url(cloudflare_process)

        # Keep script running
        print("[INFO] Servers are running. Press Ctrl+C to stop.\n")

        # Wait for processes
        for name, process in processes:
            process.wait()

    except KeyboardInterrupt:
        print("\n\n[STOP] Shutting down servers...")

        # Terminate all processes
        for name, process in processes:
            try:
                print(f"[STOP] Stopping {name}...")
                if os.name == 'nt':  # Windows
                    process.terminate()
                else:
                    process.send_signal(signal.SIGTERM)
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass

        print("[OK] All servers stopped.")

        # Clean up
        if os.path.exists('cloudflare_url.txt'):
            os.remove('cloudflare_url.txt')

if __name__ == '__main__':
    main()
