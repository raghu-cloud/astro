import json
import requests
import logging
import os
from dotenv import load_dotenv
from ..models import AIServiceConfig
from openai import OpenAI
from deepgram import Deepgram
from .language_translation_utils import get_language_langid
import nltk
from nltk.corpus import words
import time
from influx import log_point_to_db
import subprocess
import math

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
sarvam_api_key = os.getenv("SARVAM_API_KEY")
deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def get_active_stt():
    return AIServiceConfig.objects.filter(is_active=True).first()

def generate_stt(audio_file_path, language=None):
    config = get_active_stt()
    if not config:
        return {"error": "No active STT model selected."}

    if config.stt_provider == "whisper":
        return generate_with_whisper(audio_file_path, config.stt_model_version)
    elif config.stt_provider == "sarvam_ai":
        return generate_with_sarvam_ai(audio_file_path, config.stt_model_version)


def generate_with_whisper(audio_file_path, model):
    try:
        client = OpenAI(api_key=openai_api_key)
        with open(audio_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model=model,
                file=audio_file
            )
        print("Milestone whisper")
        # language_code = transcription.get('language', 'Unknown')
        return transcription.text
    except Exception as e:
        logger.error(f"Failed to transcribe audio: {e}")
        return None
    
def generate_with_sarvam_ai(audio_file_path, model, max_retries=1):
    total_start = time.time()
    print("Sarvam ai")
    url = "https://api.sarvam.ai/speech-to-text"
    files = [
        ('file', (audio_file_path, open(audio_file_path, 'rb'), 'audio/wav'))
    ]
    headers = {
        'api-subscription-key': sarvam_api_key
    }
    print("Model", model)
    payload = {
        'model': model,
    }

    duration = get_audio_duration(audio_file_path)
    duration = float(math.ceil(duration))
    detected_language = {"en-IN":"english", "hi-IN":"hindi", "kn-IN":"kannada", "ml-IN":"malayalam", "ta-IN":"tamil"}

    attempt = 0
    while attempt <= max_retries:
        api_start = time.time()
        try:
            response = requests.post(url, headers=headers, data=payload, files=files, timeout=15)
            api_end = time.time()

            if response.status_code == 200:
                data = response.json()
                transcript = data.get('transcript')
                language_code = data.get('language_code', 'unknown')
                print("Transcript", transcript)
                print("lang code", language_code)
                total_end = time.time()

                if transcript and language_code in detected_language:
                    log_point_to_db(health_metric="stt_indic", phase='api_time', detected_language=detected_language[language_code], transcript=transcript, audio_duration=duration, model="sarvam", model_version=model, latency=api_end - api_start, success=True)
                    log_point_to_db(health_metric="stt_indic", phase='total_time', detected_language=detected_language[language_code], transcript=transcript, audio_duration=duration, model="sarvam", model_version=model, latency=total_end - total_start, success=True)
                    return transcript
                else:
                    log_point_to_db(health_metric="stt_indic", phase='api_time', detected_language=f"uncertain_{language_code}", transcript=transcript, audio_duration=duration, model="sarvam", model_version=model, latency=api_end - api_start, success=True)
                    log_point_to_db(health_metric="stt_indic", phase='total_time', detected_language=f"uncertain_{language_code}", transcript=transcript, audio_duration=duration, model="sarvam", model_version=model, latency=total_end - total_start, success=True)
                    return "uncertain_audio_language"

            else:
                print(f"Attempt {attempt + 1}: Request failed with status code {response.status_code}")
                log_point_to_db(health_metric="stt_indic", phase='api_time', detected_language="unknown", transcript=None, audio_duration=duration, model="sarvam", model_version=model, latency=api_end - api_start, success=False)

        except requests.RequestException as e:
            api_end = time.time()
            print(f"Attempt {attempt + 1}: Request failed due to exception: {e}")
            log_point_to_db(health_metric="stt_indic", phase='api_time', detected_language="unknown", transcript=None, audio_duration=duration, model="sarvam", model_version=model, latency=api_end - api_start, success=False)

        attempt += 1
        time.sleep(1)  # Optional: brief pause before retry

    # If all retries failed
    total_end = time.time()
    log_point_to_db(health_metric="stt_indic", phase='total_time', detected_language="unknown", transcript=None, audio_duration=duration, model="sarvam", model_version=model, latency=total_end - total_start, success=False)
    return "uncertain_audio_language"

async def generate_with_deepgram_en(audio_file_path, model):
    total_start = time.time()
    deepgram = Deepgram(deepgram_api_key)
    with open(audio_file_path, "rb") as audio:
        source = {"buffer": audio, "mimetype": "audio/wav"}

        stt_api_start = time.time()
        response = await deepgram.transcription.prerecorded(
            source,
            options={
                "detect_language": True,
                "model": model
            }
        )
        stt_api_end = time.time()
        print(json.dumps(response, indent=4))

        # Extract transcription
        transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]
        print("Transcription:", transcript)
        duration = response["metadata"]["duration"]


        # Extract detected language
        metadata = response.get("metadata", {})
        detected_language = response["results"]["channels"][0]["detected_language"]
        # print("Detected Language:", detected_language)
        if not transcript.strip():
            detected_language = "not_english"
        else:
            if detected_language == 'en':
                flag=0
                transcript_splitted = transcript.split()
                if len(transcript_splitted)>5:
                    for i in range(0,5):
                        bool_check = is_common_english_word(transcript_splitted[i])
                        if bool_check == False:
                            flag=1
                            break
                else:
                    for word in transcript_splitted:
                        bool_check = is_common_english_word(word)
                        if bool_check == False and (word!= 'hallo' or word!='alo'):
                            flag=1
                            break
                if flag == 1:
                    detected_language = 'not_english'
            elif detected_language!='en':
                count=0
                flag=0
                transcript_splitted = transcript.split()
                if len(transcript_splitted)>5:
                    for i in range(0,5):
                        bool_check = is_common_english_word(transcript_splitted[i])
                        if bool_check == False:
                            # flag=1
                            count = count+1
                            # break
                else:
                    for word in transcript_splitted:
                        bool_check = is_common_english_word(word)

                        if bool_check == False and (word!= 'hallo' or word!='alo'):
                            # flag=1
                            count = count + 1
                            # break
                if count>1:
                    flag = 1
                    
                if flag == 0:
                    detected_language = 'en'

        print(detected_language)
        if detected_language== 'en':
            log_detected_language = 'english'
        else:
            log_detected_language = detected_language
            
        language_confidence = response["results"]["channels"][0]["language_confidence"]
        
        if response:
            log_point_to_db(health_metric="stt_english", phase="api_time", detected_language=log_detected_language, transcript= transcript,audio_duration=duration, latency= stt_api_end-stt_api_start, model="Deepgram", model_version=model, success= True)
        else:
            log_point_to_db(health_metric="stt_english", phase="api_time", detected_language=log_detected_language, transcript= transcript,audio_duration=duration, latency= stt_api_end-stt_api_start, model="Deepgram", model_version=model, success= False)
        
        total_end = time.time()
        if response and detected_language:
            log_point_to_db(health_metric="stt_english", phase="total_time", detected_language=log_detected_language, transcript=transcript,audio_duration=duration, latency= total_end-total_start, model="Deepgram", model_version=model, success= True)
        else:
            log_point_to_db(health_metric="stt_english", phase="total_time", detected_language=log_detected_language, transcript=transcript,audio_duration=duration, latency= total_end-total_start, model="Deepgram", model_version=model, success= False)
            


        return transcript, detected_language, language_confidence


# def get_language_langid_stt(text):
#     langid.set_languages(["en", "hi"])
#     lang, confidence = langid.classify(text)
#     print(f"Confidence Score: {confidence}")
#     return lang

def is_common_english_word(word):
    """Check if a word is a common English word."""
    nltk.download('words')
    return word.lower() in words.words()

def get_audio_duration(file_path):
    try:
        result = subprocess.run(
            [
                'ffprobe', '-v', 'error',
                '-select_streams', 'a:0',
                '-show_entries', 'stream=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                file_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return None






