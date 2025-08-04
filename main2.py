from pyrogram import Client, filters
import subprocess
import os
import re
import base64
import json
import stat

# Ensure N_m3u8DL-RE is executable
os.chmod("N_m3u8DL-RE", os.stat("N_m3u8DL-RE").st_mode | stat.S_IEXEC)

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("drm_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def extract_keys_from_url(url):
    if "#keysV1=" not in url:
        return None, None
    keys_raw = url.split("#keysV1=")[1]
    try:
        decoded = base64.urlsafe_b64decode(keys_raw + '==').decode()
        key_json = json.loads(decoded)
        keys = [f"{k['kid']}:{k['key']}" for k in key_json['keys']]
        return url.split("#")[0], keys
    except:
        return None, None

@app.on_message(filters.private & filters.text)
async def process_drm(client, message):
    url = message.text.strip()
    await message.reply("🔄 Processing your DRM video link...")

    clean_url, keys = extract_keys_from_url(url)
    if not clean_url or not keys:
        await message.reply("❌ Invalid link or missing keys.")
        return

    key_args = " ".join([f"--key {k}" for k in keys])
    output_name = "video_out"
    cmd = f'./N_m3u8DL-RE "{clean_url}" {key_args} --saveName "{output_name}" --workDir "{DOWNLOAD_DIR}" --autoSelect --binaryMerge'

    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError:
        await message.reply("❌ Download failed. Are the keys correct?")
        return

    for file in os.listdir(DOWNLOAD_DIR):
        if file.endswith(".mp4"):
            await message.reply_video(video=os.path.join(DOWNLOAD_DIR, file), caption="✅ Here's your video")
            os.remove(os.path.join(DOWNLOAD_DIR, file))
            return

    await message.reply("⚠️ Video file not found.")

app.run()
