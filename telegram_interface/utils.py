import os
import re
import requests
import json
import time
import logging
from django.conf import settings
import langchain_agent.utils
from dotenv import load_dotenv
from litellm import completion
from ai_services.utils.tts_utils import generate_tts
from pydub import AudioSegment
import subprocess
from ai_services.utils.language_translation_utils import get_language_langid, translate_language
from langchain_agent.models import User,Logger
from langchain_agent.models import LogType

from timing_test_csv_utils import log_time_to_csv
import influxdb_client_3
from influxdb_client_3 import InfluxDBClient3, Point, WriteOptions, WritePrecision
from datetime import datetime
from influx import log_point_to_db
from context import get_user_id


load_dotenv()
model_fallback_list = ["openai/gpt-4o-mini","gemini/gemini-2.0-flash","gemini/gemini-2.0-flash-lite","openrouter/meta-llama/llama-4-scout"]
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


INFLUX_HOST = os.getenv("INFLUX_HOST")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")


client = InfluxDBClient3(host=INFLUX_HOST, database=INFLUX_BUCKET, token=INFLUX_TOKEN)



logger = logging.getLogger(__name__)

def call_litellm(system_prompt):
    for model in model_fallback_list:
        try:
            response = completion(
  model=model,
  messages=[{ "content": system_prompt,"role": "user"}]

) 
            
            break
        except Exception as e:
            print(f"error occurred: {e}")
    content=response.choices[0].message.content
    content=content.replace('*','')
    content=content.replace('#','')

    
    return content, model

def get_audio_duration(file_path):
    """
    Returns the duration of the audio file in seconds using ffprobe.
    """
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Failed to get duration: {e}")
        return None

def send_text_message(chat_id, text):
    """
    Sends a text message to a Telegram user.
    """
    # print(chat_id)
    if settings.LOAD_TEST_MODE:
        logger.info(f"[MOCK SEND] Skipping real Telegram message during load test.\nTo: {chat_id}\nMessage: {text}")
        Logger.objects.create(user_id=str(chat_id), message=text, log_type=LogType.SYSTEM.value, message_id="test_message_id")
        return
    print("TEXT:",text)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    if text=='dsf':
        data = {"chat_id": chat_id, "text": ''}
    else:
        data = {"chat_id": chat_id, "text": text}
    response = requests.post(url, json=data)
    response_for_log = response.json()

    
    if response_for_log.get('ok', False) and 'result' in response_for_log:
        result = response_for_log['result']
        message_text = result.get('text', text)  # Use provided text as fallback
        message_id = result.get('message_id')
        
        if message_id:  # Only create log if we have a message_id
            Logger.objects.create(
                user_id=str(chat_id),
                message=message_text,
                log_type=LogType.SYSTEM.value,
                message_id=message_id
            )
    else:
        logger.error(f"Failed to send message to Telegram: {response_for_log}")
    
    print("Telegram Response:", response.json())
    return response.json()


def process_telegram_message(body, memory):
    """Processes and replies to incoming Telegram messages."""
    message = body.get("message", {})
    msg_id = message['message_id']
    msg_type = "text"
    print("MESSAGE:", message)
    languages = {'en': "english", 'kn':"kannada", 'hi':"hindi", 'ml':"malayalam", 'ta': "tamil"}
    english_translated_text =''
    user_language_response =''
    lang_not_supported_msg = "Sorry , the bot couldnt get that.This bot currently supports English, Hindi, Kannada, Malayalam, Tamil."
    
    if "text" in message:
        chat_id = message["chat"]["id"]
        user_message = message["text"]
        print("User Message:", user_message)
        language_code = get_language_langid(user_message)
        print("language code:", language_code)
        if language_code not in languages.keys():
            send_text_message(chat_id, lang_not_supported_msg)
            logger.warning("Language not supported")
            return True
        language = languages[language_code]
        if language!="english":
            translation_p1_start = time.time()
            english_translated_text = translate_language(user_message, language, "english", 1)
            translation_p1_end = time.time()
        else:
            english_translated_text = user_message

        langraph_start = time.time()
        response = langchain_agent.utils.run_llm_pipeline(english_translated_text, memory, platform="telegram", chat_id=chat_id, message_id=msg_id, user_message_type=msg_type)
        langraph_end = time.time()
        if response:
            log_point_to_db(health_metric= "langgraph_pipeline", phase="total_time", latency= langraph_end-langraph_start, success = True)
        else:
            log_point_to_db(health_metric= "langgraph_pipeline", phase="total_time", latency= langraph_end-langraph_start, success = False)
        if settings.LOAD_TEST_MODE and response:
            log_time_to_csv(chat_id, "text", msg_id, "langraph_pipeline_time", langraph_end - langraph_start)



        if language!="english":
            translation_p2_start = time.time()
            user_language_response = translate_language(response, "english", language, 2)
            translation_p2_end = time.time()

            if settings.LOAD_TEST_MODE:
                log_time_to_csv(chat_id, "text", msg_id, "language_translation", ((translation_p2_end-translation_p2_start)+(translation_p1_end-translation_p1_start)))
        else:
            user_language_response = response

        if user_language_response:
            send_text_message(chat_id, user_language_response)
            return True
            
    return False


def send_telegram_document(chat_id, file_path):
    """Sends a document (PDF) to a Telegram chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

    if settings.LOAD_TEST_MODE:
        logger.info(f"[MOCK SEND] Skipping real Telegram pdf document sending during load test.\nTo: {chat_id}\nMessage: PDF Document")
        Logger.objects.create(user_id=str(chat_id), message="PDF Document", log_type=LogType.SYSTEM.value, message_id="test_message_id")
        return
    
    with open(file_path, 'rb') as file:
        response = requests.post(url, data={"chat_id": chat_id}, files={"document": (file_path.replace(f"{chat_id}_", ""),file)})
    # os.remove(file_path)
    response_for_log = response.json()
    if response_for_log.get('ok', False) and 'result' in response_for_log:
        result = response_for_log['result']
        message_id = result.get('message_id')
        document = result.get('document', {})
        file_name = document.get('file_name', 'document')
        # user_id = get_user_id()
        # for i in range(1,20):
        #     os.remove(f"page{i}_mp_{user_id}.pdf")
        
        # Only create log if we have a message_id
        if message_id:
            Logger.objects.create(
                user_id=str(chat_id),
                message=f"Document sent: {file_name}",
                log_type=LogType.SYSTEM.value,
                message_id=message_id
            )
    else:
        logger.error(f"Failed to send document to Telegram: {response_for_log}")
    
    print("Telegram Document Response:", response.json())
    return response.json()


# def download_telegram_voice(file_id):
#     """
#     Downloads a voice message from Telegram using the file_id.
#     """
#     try:
#         file_info_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
#         file_info_response = requests.get(file_info_url)
#         file_info_response.raise_for_status()
#         file_info = file_info_response.json()

#         if not file_info["ok"]:
#             print("Failed to get file info:", file_info)
#             return None

#         file_path = file_info["result"]["file_path"]

#         file_download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
#         file_response = requests.get(file_download_url)
#         file_response.raise_for_status()

#         local_filename = f"telegram_voice{file_id}.ogg" 

#         with open(local_filename, "wb") as file:
#             file.write(file_response.content)

#         print(f"Downloaded Telegram voice message: {local_filename}")
#         return local_filename

#     except Exception as e:
#         print(f"Error downloading voice message: {e}")
#         return None
# def download_telegram_voice(file_id):
#     """
#     Downloads a voice message from Telegram using the file_id and converts it to WAV format.
#     """
#     try:
#         file_info_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
#         file_info_response = requests.get(file_info_url)
#         file_info_response.raise_for_status()
#         file_info = file_info_response.json()

#         if not file_info["ok"]:
#             print("Failed to get file info:", file_info)
#             return None

#         file_path = file_info["result"]["file_path"]

#         file_download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
#         file_response = requests.get(file_download_url)
#         file_response.raise_for_status()

#         local_ogg_filename = f"telegram_voice_{file_id}.ogg"
#         with open(local_ogg_filename, "wb") as file:
#             file.write(file_response.content)

#         print(f"Downloaded Telegram voice message: {local_ogg_filename}")

#         audio = AudioSegment.from_file(local_ogg_filename, format="ogg")
#         local_wav_filename = f"telegram_voice_{file_id}.wav"
#         audio.export(local_wav_filename, format="wav")

#         print(f"Converted to WAV format: {local_wav_filename}")
#         return local_wav_filename

#     except Exception as e:
#         print(f"Error processing voice message: {e}")
#         return None
def download_telegram_voice(file_id, chat_id):
    """
    Downloads a voice message from Telegram using the file_id and converts it to WAV format using FFmpeg.
    """
    try:
        # Fetch file information from Telegram
        file_info_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
        file_info_response = requests.get(file_info_url)
        file_info_response.raise_for_status()
        file_info = file_info_response.json()

        if not file_info["ok"]:
            print("Failed to get file info:", file_info)
            return None

        file_path = file_info["result"]["file_path"]

        # Download the OGG file
        file_download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
        file_response = requests.get(file_download_url)
        file_response.raise_for_status()

        local_ogg_filename = f"telegram_voice_{file_id}_{chat_id}.ogg"
        with open(local_ogg_filename, "wb") as file:
            file.write(file_response.content)

        print(f"Downloaded Telegram voice message: {local_ogg_filename}")

        duration = get_audio_duration(local_ogg_filename)
        print(f"Audio duration: {duration:.2f} seconds")

        # Convert OGG to WAV using FFmpeg
        local_wav_filename = f"telegram_voice_{file_id}_{chat_id}.wav"
        ffmpeg_command = [
            'ffmpeg',  '-y', '-i', local_ogg_filename, local_wav_filename
        ]
        subprocess.run(ffmpeg_command, check=True)

        print(f"Converted to WAV format: {local_wav_filename}")

        
        return local_wav_filename

    except Exception as e:
        print(f"Error processing voice message: {e}")
        return None

def process_telegram_message_audio_transcript(body, memory, file_id):
    """Processes a transcribed Telegram voice message and responds with an audio reply."""
    message = body.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    msg_id = message.get("message_id", {})
    msg_type ="voice"
    user_message = message.get("text", "")
    audio_rerequest_msg = "Sorry , i couldnt get that. Can you please try speaking again?This bot currently supports English, Hindi, Kannada, Malayalam, Tamil."
    if user_message == "uncertain_audio_language":
        send_text_message(chat_id, audio_rerequest_msg)
        logger.warning("Language not supported")
        return True
    if not chat_id or not user_message:
        logger.error("Invalid Telegram message format.")
        return False

    logger.info(f"Processing transcribed message from {chat_id}: {user_message}")
    languages = {'en': "english", 'kn':"kannada", 'hi':"hindi", 'ml':"malayalam", 'ta': "tamil"}
    english_translated_text =''
    user_language_response =''
    print("User message:",user_message)
    language_code = get_language_langid(user_message)
    print("language code:", language_code)
    language = languages[language_code]
    if not language:
        
        send_text_message(chat_id, audio_rerequest_msg)
        logger.log("Language not supported")
        return
    if language!="english":
        translation_p1_start = time.time()
        english_translated_text = translate_language(user_message, language, "english", 1)
        translation_p1_end = time.time()
    else:
        english_translated_text = user_message
    langraph_start = time.time()
    response = langchain_agent.utils.run_llm_pipeline(english_translated_text, memory,platform="telegram", chat_id=chat_id, message_id=msg_id, user_message_type="voice")
    langraph_end = time.time()
    if response:
        log_point_to_db(health_metric= "langgraph_pipeline", phase="total_time", latency= langraph_end-langraph_start, success = True)
    else:
        log_point_to_db(health_metric= "langgraph_pipeline", phase="total_time", latency= langraph_end-langraph_start, success = False)
    if settings.LOAD_TEST_MODE and response:
        log_time_to_csv(chat_id, "voice", msg_id, "langraph_pipeline_time", langraph_end - langraph_start)

    if len(response.split()) > 130:
        # llm = get_selected_llm()
        summarization_start = time.time()
        system_prompt = "You are a good summarizer. Please summarize the following text in 130 words while keeping the important details: " + response
        voice_response, model =call_litellm(system_prompt)
        summarization_end = time.time()
        model_version = model.split('/')[1]
        model = model.split('/')[0]
        if voice_response:
            log_point_to_db(health_metric="response_summarization", phase="llm_time", latency= summarization_end-summarization_start, model=model, model_version=model_version, success=True)
        else:
            log_point_to_db(health_metric="response_summarization", phase="llm_time", latency= summarization_end-summarization_start, model=model, model_version=model_version, success=False)

        if settings.LOAD_TEST_MODE and voice_response:
            log_time_to_csv(chat_id, "voice", msg_id, "summarization_for_voice", summarization_end-summarization_start)
        # voice_response=response.choices[0].message.content
    else:
        voice_response = response
    if language!="english":
        translation_p2_start = time.time()
        user_language_response = translate_language(response, "english", language, 2)
        if voice_response != response:
            user_language_voice_response = translate_language(voice_response, "english" , language, 3)
        else:
            user_language_voice_response = user_language_response
        translation_p2_end = time.time()
        if settings.LOAD_TEST_MODE:
            log_time_to_csv(chat_id, "voice", msg_id, "language_translation", ((translation_p2_end-translation_p2_start)+(translation_p1_end-translation_p1_start)))
    else :
        user_language_response = response
        user_language_voice_response = voice_response
    
    tts_start = time.time()
    audio_file = generate_tts(user_language_voice_response, chat_id, language)
    tts_end = time.time()
    if settings.LOAD_TEST_MODE and voice_response:
        log_time_to_csv(chat_id, "voice", msg_id, "TTS", (tts_end - tts_start))

    if not audio_file:
        logger.error("Failed to generate audio file.")
        return
    # print("USER LANGUAGE RESPONSE", user_language_response)
    # print("USER LANAGUAGE VOICE RESPONSE", user_language_voice_response)
    audio_send_start = time.time()
    send_success = send_telegram_audio(chat_id, audio_file)
    audio_send_end = time.time()
    if settings.LOAD_TEST_MODE:
        log_time_to_csv(chat_id, "voice", msg_id, "audio_send_time", audio_send_end-audio_send_start)
    if send_success:
        logger.info(f"Audio response sent successfully to {chat_id}.")
        send_text_message(chat_id, user_language_response)
        # Delete the OGG file after conversion
        try:
            os.remove(f"telegram_voice_{file_id}_{chat_id}.ogg")
            print(f"Deleted OGG file: telegram_voice_{file_id}_{chat_id}.ogg")
        except Exception as e:
            print(f"Failed to delete OGG file: telegram_voice_{file_id}_{chat_id}.ogg :{e}")


        try:
            os.remove(f"telegram_voice_{file_id}_{chat_id}.wav")
            print(f"Deleted file: telegram_voice_{file_id}_{chat_id}.wav")
        except Exception as e:
            print(f"Failed to delete file: telegram_voice_{file_id}_{chat_id}.wav: {e}")


        try:
            os.remove(f"{chat_id}_tts_output.wav")
            print(f"Deleted file: {chat_id}_tts_output.wav")
        except Exception as e:
            print(f"Failed to delete file: {chat_id}_tts_output.wav: {e}")


        return True
    
    
    else:
        logger.error(f"Failed to send audio response to {chat_id}.")
        return False


def send_telegram_audio(chat_id, file_path):
    """
    Uploads an audio file and sends it as a voice message to the user.
    """
    if not os.path.exists(file_path):
        logger.error(f"Audio file not found: {file_path}")
        return False

    if settings.LOAD_TEST_MODE:
        logger.info(f"[MOCK SEND] Skipping real Telegram audio sending during load test.\nTo: {chat_id}\nMessage: voice message")
        Logger.objects.create(user_id=str(chat_id), message="voice_message", log_type=LogType.SYSTEM.value, message_id="test_message_id")
        return True
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVoice"
    
    with open(file_path, "rb") as audio_file:
        files = {"voice": audio_file}
        data = {"chat_id": chat_id}

        response = requests.post(url, data=data, files=files)
        
        if response.status_code == 200:
            logger.info(f"Audio message sent successfully to {chat_id}.")
            return True
        else:
            logger.error(f"Failed to send audio message. Response: {response.text}")
            return False
        
def send_typing_action(chat_id, stop_event):
    """Continuously sends typing action every 4 seconds until stop_event is set"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendChatAction"
    data = {"chat_id": chat_id, "action": "typing"}
    
    while not stop_event.is_set():
        try:
            requests.post(url, json=data)
            # Telegram's typing indicator lasts ~5 seconds
        except Exception as e:
            print(f"Error sending typing action: {e}")
            break
        stop_event.wait(timeout=4)

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


def send_text_message_with_buttons(chat_id, text, buttons):
    """
    Sends a text message to a Telegram user with inline keyboard buttons.
    buttons should be a list of lists, where each inner list represents a row of buttons.
    Each button is a dictionary with 'text' and 'callback_data' keys.
    """
    if settings.LOAD_TEST_MODE:
        logger.info(f"[MOCK SEND] Skipping real Telegram message during load test.\nTo: {chat_id}\nMessage: {text}\nButtons: {buttons}")
        Logger.objects.create(user_id=str(chat_id), message=text, log_type=LogType.SYSTEM.value, message_id="test_message_id")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # Create inline keyboard markup
    keyboard = []
    for row in buttons:
        keyboard_row = []
        for button in row:
            keyboard_row.append({
                "text": button['text'],
                "callback_data": button['callback_data']
            })
        keyboard.append(keyboard_row)

    data = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {
            "inline_keyboard": keyboard
        }
    }

    response = requests.post(url, json=data)
    response_for_log = response.json()

    if response_for_log.get('ok', False) and 'result' in response_for_log:
        result = response_for_log['result']
        message_text = result.get('text', text)
        message_id = result.get('message_id')

        if message_id:
            Logger.objects.create(
                user_id=str(chat_id),
                message=message_text,
                log_type=LogType.SYSTEM.value,
                message_id=message_id
            )
    else:
        logger.error(f"Failed to send message with buttons to Telegram: {response_for_log}")

    return response.json()

# def log_point_to_db(
#     point: Point,
#     health_metric: str,
#     phase: str = None,
#     translation_from: str = None,
#     translation_to: str = None,
#     latency: float = None,
#     model: str = None,
#     success: bool = None
    
# ):

#     point = Point("usage_metrics").time(datetime.utcnow(), WritePrecision.NS)
#     point = point.tag("health_metric_category", health_metric)

#     if phase:
#         point = point.tag("phase", phase)

#     if model:
#         point = point.tag("model", model)

#     if translation_from is not None:
#         point = point.tag("translation_from", translation_from)

#     if translation_to is not None:
#         point = point.tag("translation_to", translation_to)

#     if latency is not None:
#         point = point.field("latency", round(latency, 4))

#     if success is not None:
#         point = point.field("success", str(success).lower())  # Store as 'true' or 'false'

#     point = point.time(datetime.now(), WritePrecision.S)

#     client.write( record=point, write_precision='s')


