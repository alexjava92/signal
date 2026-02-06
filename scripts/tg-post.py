#!/usr/bin/env python3
"""Send a post to the signal Telegram channel."""
import os
import sys
import requests
import json

# Load .env
env = {}
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip()

TOKEN = env.get('TG_TOKEN', '')
CHANNEL = env.get('TG_CHANNEL', '@signal_claude_code')
API = f"https://api.telegram.org/bot{TOKEN}"


def send_photo(image_path, caption):
    with open(image_path, "rb") as f:
        r = requests.post(
            f"{API}/sendPhoto",
            data={"chat_id": CHANNEL, "caption": caption, "parse_mode": "HTML"},
            files={"photo": ("image.png", f, "image/png")}
        )
    return r.json()


def send_text(text):
    r = requests.post(
        f"{API}/sendMessage",
        data={"chat_id": CHANNEL, "text": text, "parse_mode": "HTML",
              "disable_web_page_preview": False}
    )
    return r.json()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: tg-post.py <caption_file> [image_file]")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        caption = f.read().strip()

    if len(sys.argv) >= 3:
        result = send_photo(sys.argv[2], caption)
    else:
        result = send_text(caption)

    if result.get("ok"):
        print(f"OK! message_id: {result['result']['message_id']}")
    else:
        print(f"Error: {result.get('description')}")
        sys.exit(1)
