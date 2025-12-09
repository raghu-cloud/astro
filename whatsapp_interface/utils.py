import os
import json
import requests
import logging
from dotenv import load_dotenv
import langchain_agent.utils


load_dotenv()

logger = logging.getLogger(__name__)


ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
RECIPIENT_WAID = os.getenv("RECIPIENT_WAID")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
VERSION = os.getenv("VERSION")


def send_whatsapp_message():
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": "Bearer " + ACCESS_TOKEN,
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": RECIPIENT_WAID,
        "type": "template",
        "template": {"name": "hello_world", "language": {"code": "en_US"}},
    }
    response = requests.post(url, headers=headers, json=data)
    return response

def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )

def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
    }

    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"

    response = requests.post(url, data=data, headers=headers)
    if response.status_code == 200:
        print("Status:", response.status_code)
        print("Content-type:", response.headers["content-type"])
        print("Body:", response.text)
        print("Response:", response)
        return response
    else:
        print(response.status_code)
        print(response.text)
        return response
    

def is_valid_whatsapp_message(body):
    """Checks if the payload is a valid WhatsApp message."""
    try:
        messages = body.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [])
        return bool(messages)
    except Exception as e:
        logger.error(f"Error validating message: {e}")
        return False


def process_whatsapp_message(body):
    """Processes and replies to incoming WhatsApp messages."""
    messages = body["entry"][0]["changes"][0]["value"]["messages"]
    print("MESSAGU:", messages)
    for message in messages:
        from_number = message["from"]
        user_message = message.get("text", {}).get("body", "")
        print("user msgghdjdjkjdkd:", user_message)

        if user_message:
            response = langchain_agent.utils.run_llm_pipeline(user_message)
            data = get_text_message_input(RECIPIENT_WAID , response)
            send_message(data)


def upload_pdf(file_path):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/media"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    files = {
        'file': ('astro_details.pdf', open(file_path, 'rb'), 'application/pdf')
    }
    data = {
        'messaging_product': 'whatsapp'
    }
    response = requests.post(url, headers=headers, files=files, data=data)
    if response.status_code == 200:
        media_id = response.json().get('id')
        print(f"Media uploaded successfully. Media ID: {media_id}")
        return media_id
    else:
        print(f"Failed to upload media: {response.status_code} - {response.text}")
        return None
    

def send_pdf(recipient_id, media_id):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "document",
        "document": {
            "id": media_id,
            "caption": "Your Astrology Personality Report",
            "filename": "astro_details.pdf"
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print("Document sent successfully.")
    else:
        print(f"Failed to send document: {response.status_code} - {response.text}")



def download_media(media_id):
    """Downloads media (e.g., audio) using the WhatsApp Media API."""
    try:
        media_url = f"https://graph.facebook.com/{VERSION}/{media_id}"
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        response = requests.get(media_url, headers=headers)
        response.raise_for_status()
        media_data = response.json()

        media_download_url = media_data["url"]
        media_response = requests.get(media_download_url, headers=headers)
        media_response.raise_for_status()

        file_path = f"{media_id}.ogg"  
        with open(file_path, "wb") as file:
            file.write(media_response.content)

        logger.info(f"Downloaded media file: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to download media: {e}")
        return None
    

def upload_media(file_path, mime_type="audio/mp4"):
    """Uploads a media file to WhatsApp's servers and returns the media ID."""
    try:
        url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/media"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
        }
        files = {
            "file": (file_path, open(file_path, "rb"), mime_type)
        }
        data = {
            'messaging_product': 'whatsapp'
        }
        response = requests.post(url, headers=headers, files=files, data = data)
        response.raise_for_status()
        media_id = response.json()["id"]
        logger.info(f"Uploaded media file. Media ID: {media_id}")
        return media_id
    except Exception as e:
        logger.error(f"Failed to upload media: {e}")
        return None


def send_audio_message(recipient_id, media_id):
    """Sends an audio message using the WhatsApp Business API."""
    try:
        url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_id,
            "type": "audio",
            "audio": {
                "id": media_id,
            },
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        logger.info(f"Audio message sent to {recipient_id}.")
        return response.json()
    except Exception as e:
        logger.error(f"Failed to send audio message: {e}")
        return None
    

def process_whatsapp_message_audio_transcript(body):
    """Processes and replies as an audio file taking body with transcript text as input"""
    messages = body["entry"][0]["changes"][0]["value"]["messages"]
    for message in messages:
        from_number = message["from"]
        user_message = message.get("text", {}).get("body", "")

        if user_message:
            response = langchain_agent.utils.run_llm_pipeline(user_message)
            audio_file = langchain_agent.utils.text_to_speech(response)
            if audio_file:
                media_id = upload_media(audio_file)
                if media_id:
                    send_audio_message(from_number, media_id)
                else:
                    logger.error("Failed to upload audio file.")
            else:
                logger.error("Failed to generate audio file.")
            data = get_text_message_input(RECIPIENT_WAID , response)
            send_message(data)
