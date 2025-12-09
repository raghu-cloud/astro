import torch
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
import soundfile as sf
import requests
import base64
from smallest import Smallest
from ..models import AIServiceConfig
from dotenv import load_dotenv
import os
from io import BytesIO
from pydub import AudioSegment
import time
from influx import log_point_to_db
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv()
smallest_api_key = os.getenv("SMALLEST_WAVES_API_KEY")
sarvam_api_key = os.getenv("SARVAM_API_KEY")

def get_active_tts():
    return AIServiceConfig.objects.filter(is_active=True).first()

def generate_tts(text, chat_id, language=None):
    config = get_active_tts()
    if not config:
        return {"error": "No active TTS model selected."}

    if config.tts_provider == "parler_tts":
        return generate_with_parler_tts(text, config.tts_voice, language, chat_id)
    elif config.tts_provider == "smallest_ai":
        return generate_with_smallest_ai(text,  config.tts_voice, config.tts_model_version, chat_id)
    elif config.tts_provider == "sarvam_ai":
        return generate_with_sarvam_ai(text,  config.tts_voice, config.tts_model_version, chat_id, language)

    return {"error": "Invalid TTS provider."}

def generate_with_parler_tts(text, speaker, language, chat_id):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model = ParlerTTSForConditionalGeneration.from_pretrained("ai4bharat/indic-parler-tts").to(device)
    tokenizer = AutoTokenizer.from_pretrained("ai4bharat/indic-parler-tts")
    description_tokenizer = AutoTokenizer.from_pretrained(model.config.text_encoder._name_or_path)

    description = f"{speaker} has an  astrological accent and who fluently speaks {language}."
    description_input_ids = description_tokenizer(description, return_tensors="pt").to(device)
    prompt_input_ids = tokenizer(text, return_tensors="pt").to(device)

    generation = model.generate(
        input_ids=description_input_ids.input_ids,
        attention_mask=description_input_ids.attention_mask,
        prompt_input_ids=prompt_input_ids.input_ids,
        prompt_attention_mask=prompt_input_ids.attention_mask,
    )
    audio_arr = generation.cpu().numpy().squeeze()
    output_file = f"{chat_id}_tts_output.wav"
    sf.write(output_file, audio_arr, model.config.sampling_rate)
    
    return output_file

def generate_with_smallest_ai(text, voice_id, model, chat_id):
    client = Smallest(api_key=smallest_api_key)
    output_file = f"{chat_id}tts_output.wav"
    client.synthesize(text, model=model, sample_rate=24000, speed=1.0, save_as=output_file, voice_id=voice_id)
    return output_file

class SarvamTTSAPIException(Exception):
    pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type(SarvamTTSAPIException)
)
def call_sarvam_tts_api(payload, headers):
    response = requests.post("https://api.sarvam.ai/text-to-speech", json=payload, headers=headers)
    if response.status_code != 200:
        raise SarvamTTSAPIException(f"API Error: {response.status_code} - {response.text}")
    return response.json()


# def generate_with_sarvam_ai(text, speaker, model_version, chat_id, language):
#     total_start = time.time()
#     language_code ={"english":"en-IN", "kannada": "kn-IN", "hindi":"hi-IN", "malayalam": "ml-IN", "tamil": "ta-IN"}
#     success = True
#     targetlanguage_code = language_code[language]
#     char_count = len(text)
#     url = "https://api.sarvam.ai/text-to-speech"
#     headers = {"api-subscription-key": sarvam_api_key, "Content-Type": "application/json"}
#     try:
#         chunks = split_text_into_chunks(text, language)
#     except ValueError as e:
#         success = False
#         print(e)
#         total_end = time.time()
#         log_point_to_db(health_metric="tts", phase="api_time", model="sarvam", model_version=model_version,character_count=char_count, latency= 0, detected_language=language, success=success)
#         log_point_to_db(health_metric="tts", phase="total_time", model="sarvam", model_version=model_version,character_count=char_count, latency= total_end-total_start, detected_language=language, success=success)

#         exit()

#     all_audio_segments = []
#     api_time = 0
#     for batch in batch_chunks(chunks):
#         payload = {
#             "inputs": batch,
#             "target_language_code": targetlanguage_code,
#             "speaker": speaker,
#             "speech_sample_rate": 8000,
#             "enable_preprocessing": True,
#             "model": model_version
#         }
#         api_start = time.time()
#         response = requests.post(url, json=payload, headers=headers)
#         api_end = time.time()
#         api_time = api_time + (api_end-api_start)
#         if response.status_code == 200:
#             data = response.json()
#             for audio_base64 in data.get('audios', []):
#                 audio_bytes = base64.b64decode(audio_base64)
#                 audio = AudioSegment.from_wav(BytesIO(audio_bytes))
#                 all_audio_segments.append(audio)
#         else:
#             success = False
#             print(f"API Error: {response.status_code} - {response.text}")

#     log_point_to_db(health_metric="tts", phase="api_time", model="sarvam", model_version=model_version,character_count=char_count, latency= api_time, detected_language=language, success=success)
#     if all_audio_segments:
#         combined = all_audio_segments[0]
#         for audio in all_audio_segments[1:]:
#             combined += audio
#         output_file = f"{chat_id}_tts_output.wav"
#         combined.export(output_file, format="wav")
#         print(f"✅ Combined audio saved as '{output_file}'")
#         total_end = time.time()
#         log_point_to_db(health_metric="tts", phase="total_time", model="sarvam", model_version=model_version,character_count=char_count, latency= total_end-total_start, detected_language=language, success=success)
#         return output_file
#     else:
#         success = False
#         print("❌ No audio data to save")
#         total_end = time.time()
#         log_point_to_db(health_metric="tts", phase="total_time", model="sarvam", model_version=model_version,character_count=char_count, latency= total_end-total_start, detected_language=language, success=success)
#         print("❌ No audio data to save")
        
#         return {"error": "Sarvam.ai API failed."}

def generate_with_sarvam_ai(text, speaker, model_version, chat_id, language):
    total_start = time.time()
    language_code = {"english": "en-IN", "kannada": "kn-IN", "hindi": "hi-IN", "malayalam": "ml-IN", "tamil": "ta-IN"}
    success = True
    targetlanguage_code = language_code[language]
    char_count = len(text)
    headers = {"api-subscription-key": sarvam_api_key, "Content-Type": "application/json"}

    try:
        chunks = split_text_into_chunks(text, language)
    except ValueError as e:
        success = False
        print(e)
        total_end = time.time()
        log_point_to_db(health_metric="tts", phase="api_time", model="sarvam", model_version=model_version,character_count=char_count, latency= 0.0, detected_language=language, success=success)
        log_point_to_db(health_metric="tts", phase="total_time", model="sarvam", model_version=model_version,character_count=char_count, latency= total_end-total_start, detected_language=language, success=success)
        return {"error": str(e)}

    all_audio_segments = []
    api_time = 0
    for batch in batch_chunks(chunks):
        payload = {
            "inputs": batch,
            "target_language_code": targetlanguage_code,
            "speaker": speaker,
            "speech_sample_rate": 8000,
            "enable_preprocessing": True,
            "model": model_version
        }

        try:
            api_start = time.time()
            data = call_sarvam_tts_api(payload, headers)
            api_end = time.time()
            api_time = api_time + (api_end - api_start)

            for audio_base64 in data.get("audios", []):
                audio_bytes = base64.b64decode(audio_base64)
                audio = AudioSegment.from_wav(BytesIO(audio_bytes))
                all_audio_segments.append(audio)
        except SarvamTTSAPIException as e:
            print(e)
            success = False
            continue

    log_point_to_db(health_metric="tts", phase="api_time", model="sarvam", model_version=model_version,character_count=char_count, latency= float(api_time), detected_language=language, success=success)

    if all_audio_segments:
        combined = all_audio_segments[0]
        for audio in all_audio_segments[1:]:
            combined += audio
        output_file = f"{chat_id}_tts_output.wav"
        combined.export(output_file, format="wav")
        print(f"✅ Combined audio saved as '{output_file}'")
        total_end = time.time()
        log_point_to_db(health_metric="tts", phase="total_time", model="sarvam", model_version=model_version,character_count=char_count, latency= total_end-total_start, detected_language=language, success=success)
        return output_file
    else:
        print("❌ No audio data to save")
        total_end = time.time()
        log_point_to_db(health_metric="tts", phase="total_time", model="sarvam", model_version=model_version,character_count=char_count, latency= total_end-total_start, detected_language=language, success=False)
        return {"error": "Sarvam.ai API failed."}




def split_text_into_chunks(text, language, category="tts", max_chunk_length=500):
    if category == "translation":
        terminator = '.'
    sentence_terminators = {
        'hindi': '।',
        'english': '.',
        'kannada': '.',
        'malayalam': '.',
        'tamil': '.'
    }
    terminator = sentence_terminators[language]
    sentences = [s.strip() + '.' for s in text.split(terminator) if s.strip()]
    chunks = []
    current_chunk = []
    for sentence in sentences:
        temp_chunk = current_chunk + [sentence]
        temp_chunk_str = ' '.join(temp_chunk)
        if len(temp_chunk_str) > max_chunk_length:
            if current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
            else:
                raise ValueError(f"Sentence exceeds {max_chunk_length} characters: {sentence}")
        else:
            current_chunk = temp_chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks

def batch_chunks(chunks, batch_size=3):
    for i in range(0, len(chunks), batch_size):
        yield chunks[i:i + batch_size]