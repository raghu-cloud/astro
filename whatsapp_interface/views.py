from django.shortcuts import render

# Create your views here.
import os
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from dotenv import load_dotenv
import json
import requests
from .utils import is_valid_whatsapp_message, process_whatsapp_message, download_media, upload_media, send_audio_message, process_whatsapp_message_audio_transcript
# from langchain_agent.utils import generate_transcription_from_audio

load_dotenv()
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
VERIFY_TOKEN =os.getenv("VERIFY_TOKEN")
RECIPIENT_WAID = os.getenv("RECIPIENT_WAID")
logger = logging.getLogger(__name__)


def verify_webhook(request):
    """Verifies the webhook with WhatsApp (for initial setup)."""
    mode = request.GET.get("hub.mode")
    token = request.GET.get("hub.verify_token")
    challenge = request.GET.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            logger.info("WEBHOOK_VERIFIED")
            # Return the challenge as plain text
            return HttpResponse(challenge, content_type="text/plain", status=200)
        logger.warning("VERIFICATION_FAILED")
        return JsonResponse({"error": "Verification failed"}, status=403)
    
    logger.error("MISSING_PARAMETER")
    return JsonResponse({"error": "Missing parameters"}, status=400)


# def handle_message(request):
#     """Handles incoming messages and status updates from WhatsApp."""
#     try:
#         body = json.loads(request.body)
#         logger.info(f"Incoming payload: {body}")

#         if body.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("statuses"):
#             logger.info("Received a WhatsApp status update.")
#             return JsonResponse({"status": "ok"}, status=200)

#         if is_valid_whatsapp_message(body):
#             process_whatsapp_message(body)
#             return JsonResponse({"status": "ok"}, status=200)

#         logger.error("Invalid WhatsApp event received.")
#         return JsonResponse({"error": "Not a valid WhatsApp API event"}, status=404)
#     except json.JSONDecodeError as e:
#         logger.error(f"Failed to parse JSON: {e}")
#         return JsonResponse({"error": "Invalid JSON"}, status=400)

def handle_message(request):
    """Handles incoming messages and status updates from WhatsApp."""
    try:
        body = json.loads(request.body)
        logger.info(f"Incoming payload: {body}")

        
        if body.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("statuses"):
            logger.info("Received a WhatsApp status update.")
            return JsonResponse({"status": "ok"}, status=200)

        # Check if it's a valid message
        if is_valid_whatsapp_message(body):
            message = body["entry"][0]["changes"][0]["value"]["messages"][0]
            from_number = message["from"]

            if message["type"] == "text":
                # Handle text message
                message_body = message["text"]["body"]
                logger.info(f"Received text message from {from_number}: {message_body}")
                response_text = process_whatsapp_message(body)  # Generate response text

                # # Convert response text to speech
                # audio_file = text_to_speech(response_text)
                # if audio_file:
                #     # Upload the audio file
                #     media_id = upload_media(audio_file)
                #     if media_id:
                #         # Send the audio message
                #         send_audio_message(from_number, media_id)
                #     else:
                #         logger.error("Failed to upload audio file.")
                # else:
                #     logger.error("Failed to generate audio file.")

            elif message["type"] == "audio":
                # Handle voice message
                media_id = message["audio"]["id"]
                logger.info(f"Received voice message from {from_number}. Media ID: {media_id}")

                # Download the audio file
                file_path = download_media(media_id)
                if file_path:
                    # Transcribe the audio
                    transcription = "test"
                    # transcription = generate_transcription_from_audio(file_path)
                    if transcription:
                        logger.info(f"Transcription: {transcription}")
                        # Process the transcription as a text message
                        response_text = process_whatsapp_message_audio_transcript({
                            "entry": [
                                {
                                    "changes": [
                                        {
                                            "value": {
                                                "messages": [
                                                    {
                                                        "from": from_number,
                                                        "text": {"body": transcription},
                                                        "type": "text"
                                                    }
                                                ]
                                            }
                                        }
                                    ]
                                }
                            ]
                        })
                    else:
                        logger.error("Failed to transcribe audio.")
                else:
                    logger.error("Failed to download audio file.")

            return JsonResponse({"status": "ok"}, status=200)

        logger.error("Invalid WhatsApp event received.")
        return JsonResponse({"error": "Not a valid WhatsApp API event"}, status=404)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        return JsonResponse({"error": "Invalid JSON"}, status=400)