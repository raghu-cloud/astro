import requests
import logging
import os
from dotenv import load_dotenv
from ..models import AIServiceConfig
import asyncio
import langid
import re
from ai_services.utils.tts_utils import split_text_into_chunks
from ai_services.models import AIServiceConfig
import time
from influx import log_point_to_db

load_dotenv()
sarvam_api_key = os.getenv("SARVAM_API_KEY")

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

langid.set_languages(["en", "hi", "kn", "ml", "ta"])

def get_active_translation_model():
    return AIServiceConfig.objects.filter(is_active=True).first()

def translate_language(text, source_language, target_language, phase):
    config = get_active_translation_model()
    if not config:
        return {"error": "No active STT model selected."}

    if config.translation_provider == "sarvam_ai":
        return translate_with_sarvam(text,source_language, target_language, config.translation_model_version, phase)
    
def translate_with_sarvam(text, source_language, target_language, model, phase):

    translation_total_start = time.time()
    url = "https://api.sarvam.ai/translate"
    language_code = {
        "english": "en-IN", "kannada": "kn-IN", "hindi": "hi-IN",
        "malayalam": "ml-IN", "tamil": "ta-IN"
    }
    sourcelanguage_code = language_code[source_language]
    targetlanguage_code = language_code[target_language]
    char_count = len(text)

    try:
        chunks = split_text_into_chunks(text, source_language, "translation", max_chunk_length=1000)
    except ValueError as e:
        print(f"Chunking error: {e}")
        return None

    translated_segments = []
    headers = {
        "api-subscription-key": sarvam_api_key,
        "Content-Type": "application/json"
    }
    api_time = 0.0
    success = True
    for chunk in chunks:
        payload = {
            "input": chunk,
            "source_language_code": sourcelanguage_code,
            "target_language_code": targetlanguage_code,
            "speaker_gender": "Male",
            "mode": "formal",
            "model": model,
            "enable_preprocessing": False,
            "numerals_format": "native"
        }
        for attempt in range(3):  # Retry up to 3 times
            api_time_start = time.time()
            response = requests.post(url, json=payload, headers=headers)
            api_time_end = time.time()
            api_time = api_time + (api_time_end - api_time_start)

            if response.status_code == 200:
                data = response.json()
                translated_text = data.get('translated_text')
                translated_segments.append(translated_text)
                break
            else:
                print(f"Attempt {attempt + 1}: Request failed with status code {response.status_code}")
                if attempt == 2:  # After final retry
                    success = False
                    break

        if not success:
            break

    combined_text = ''.join(translated_segments) if translated_segments else None
    refined_translated_text = normalize_sentence_dots(combined_text) if combined_text else None


    # Log metrics (same as your original code)
    for suffix in ["api_time", "total_time"]:
        latency = api_time if suffix == "api_time" else (time.time() - translation_total_start)
        log_point_to_db(
            health_metric="translation",
            phase=f"translation_phase{phase}_{suffix}",
            latency=latency,
            character_count=char_count,
            model="sarvam",
            model_version=model,
            translation_from=source_language,
            translation_to=target_language,
            success=success
        )

    config = AIServiceConfig.objects.filter(is_active=True).first()
    speaker = config.tts_voice
    if speaker in ["arvind", "arjun"] and refined_translated_text:
        refined_translated_text = refined_translated_text.replace("सकती हूँ", "सकता हूँ") 

    print("Translated text", refined_translated_text)
    return refined_translated_text if success else None



def get_language_langid(text):
    langid.set_languages(["en", "hi", "kn", "ml", "ta","te"])
    lang, confidence = langid.classify(text)
    print(f"Confidence Score: {confidence}")
    return lang


def normalize_sentence_dots(text):
    """Replace multiple dots following sentence terminators with single dot"""
    # Match sentence terminators (। or .) followed by whitespace and multiple dots
    pattern = r'([।.])\s*\.+'
    
    # Replace with just the original sentence terminator
    return re.sub(pattern, r'\1', text)
