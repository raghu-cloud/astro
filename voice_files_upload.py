import os
import json
import requests
from dotenv import load_dotenv


load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

CHAT_ID = 5623945984



def upload_voice_and_get_file_id(chat_id: int, voice_file_path: str, delete_after: bool = True):
    send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVoice"

    with open(voice_file_path, "rb") as voice_file:
        files = {
            "voice": voice_file
        }
        data = {
            "chat_id": chat_id,
            "caption": "Voice upload for load testing"
        }

        response = requests.post(send_url, data=data, files=files)

    if response.status_code == 200:
        result = response.json()["result"]
        file_id = result["voice"]["file_id"]
        message_id = result["message_id"]
        print(f"✅ Uploaded `{os.path.basename(voice_file_path)}` — file_id: {file_id}")

        # Optional: delete the message
        if delete_after:
            delete_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage"
            del_data = {
                "chat_id": chat_id,
                "message_id": message_id
            }
            del_res = requests.post(delete_url, data=del_data)
            if del_res.status_code == 200:
                print("🗑️  Deleted message after upload.")
            else:
                print("⚠️  Failed to delete message:", del_res.text)

        return file_id
    else:
        print("❌ Upload failed:", response.text)
        return None
    


def upload_all_voice_samples(chat_id: int, folder="voice_samples", delete_after=True):
    voice_file_ids = {}
    for filename in os.listdir(folder):
        if filename.endswith(".ogg"):
            file_path = os.path.join(folder, filename)
            file_id = upload_voice_and_get_file_id(chat_id, file_path, delete_after)
            if file_id:
                voice_file_ids[filename] = file_id

    # Save to JSON for use in load tests
    with open("voice_file_ids.json", "w") as f:
        json.dump(voice_file_ids, f, indent=2)
    print("✅ All file_ids saved to voice_file_ids.json")

upload_all_voice_samples(CHAT_ID)