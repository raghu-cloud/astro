from ninja import NinjaAPI
from .utils import  run_llm_pipeline, test
from .schemas import ChatRequest, VoiceChatResponse, KundliRequest, PanchangRequest, OnboardingRequest
from ninja.files import UploadedFile
import os
import uuid
from whatsapp_interface.utils import send_whatsapp_message
from langchain_agent.pdf_utils.api_utils import handle_generate_kundli, handle_panchang_details
from pydantic import BaseModel
from langchain_agent.models import User, UserProfile, Logger, LogType
from django.db import models as django_models
from .pdf_utils.generate_pdf import generate_horoscope
from ai_services.utils.stt_utils import generate_stt
from ai_services.utils.tts_utils import generate_tts
from ai_services.utils.language_translation_utils import get_language_langid, translate_language
import tempfile
from django.http import FileResponse, HttpResponse
import time
import asyncio
from influx import log_point_to_db
from litellm import completion
from ai_services.utils.stt_utils import generate_with_deepgram_en
import subprocess
import boto3
from dotenv import load_dotenv

load_dotenv()

# Initialize S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

api = NinjaAPI()

# @api.post("/chat_text")
# def chat(request, payload: ChatRequest):
#     response_text = run_llm_pipeline(payload.user_message)
#     whatsapp_response = send_whatsapp_message(response_text,payload.phone_number)
#     return {"response": response_text, "whatsapp": whatsapp_response}



# @api.post("/voice-chat", response=VoiceChatResponse)
# def voice_chat(request, file: UploadedFile, phone : str):

#     temp_path = f"/tmp/{file.name}"
#     with open(temp_path, "wb") as f:
#         f.write(file.read())
    
#     transcription_text = generate_transcription_from_audio(temp_path)
    
#     os.remove(temp_path)
    
#     response_text = run_llm_pipeline(transcription_text)
#     whatsapp_response = send_whatsapp_message(response_text,phone)
    
#     return VoiceChatResponse(transcription=transcription_text, response=response_text, whatsapp=whatsapp_response)


@api.post("/generate-kundli")
def generate_kundli(request, payload: KundliRequest):
    try:
        random_user_id = str(uuid.uuid4())
        s3_url = handle_generate_kundli(payload.details.model_dump(), random_user_id)
        if "error" in s3_url:
            return api.create_response(request, s3_url , status=400)
        return {"pdf_url": s3_url}
    except Exception as e:
        return {"error": str(e)}
    

@api.post("/show-panchang")
def show_panchang(request, payload: PanchangRequest):
    try:
        panchang_result_json = handle_panchang_details(payload.details.model_dump())
        if "error" in panchang_result_json:
            return api.create_response(request, panchang_result_json , status=400)
        return panchang_result_json
    except Exception as e:
        return {"error": str(e)}

class SendMessageRequest(BaseModel):
    message: str
@api.post("/send_message")
def send_message(request, payload: SendMessageRequest):
    try:
        user_id = clerk_authentication(request)
        
        # Get the last (maximum) message_id from all Logger entries
        max_message_id = Logger.objects.aggregate(django_models.Max('message_id'))['message_id__max']
        
        # If this is the first message, start with "1", otherwise increment by 1
        if max_message_id is None:
            message_id = "1"
        else:
            message_id = str(int(max_message_id) + 1)
        
        # Create user log entry with the new message_id
        Logger.objects.create(
            user_id=user_id, 
            message=payload.message, 
            log_type=LogType.USER.value,
            message_id=message_id
        )

        # Get system response
        message = test(payload.message, user_id)
        max_message_id = Logger.objects.aggregate(django_models.Max('message_id'))['message_id__max']
        
        # If this is the first message, start with "1", otherwise increment by 1
        if max_message_id is None:
            message_id = "1"
        else:
            message_id = str(int(max_message_id) + 1)
        
        # Create system log entry with the same message_id
        Logger.objects.create(
            user_id=user_id, 
            message=message, 
            log_type=LogType.SYSTEM.value,
            message_id=message_id
        )
        
        return message
    except Exception as e:
        return {"error": str(e)}


@api.post("/send_audio")
def send_audio(request, audio: UploadedFile):
    """
    Handle audio message uploads (mimicking telegram_interface voice handling):
    1. Receives audio file from client
    2. Transcribes audio to text using STT
    3. Detects language and translates to English if needed
    4. Processes through chatbot pipeline
    5. Summarizes response if too long (for voice)
    6. Translates response back to user's language
    7. Returns text response (or PDF URL if kundli is generated)
    """
    temp_audio_path = None
    original_audio_path = None
    
    try:
        user_id = clerk_authentication(request)
        
        # Language configuration
        languages = {'en': "english", 'kn': "kannada", 'hi': "hindi", 'ml': "malayalam", 'ta': "tamil"}
        audio_rerequest_msg = "Sorry, I couldn't understand that. Please try speaking again. This bot currently supports English, Hindi, Kannada, Malayalam, Tamil."
        
        # Create a temporary file to store the uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio.name)[1]) as temp_audio:
            for chunk in audio.chunks():
                temp_audio.write(chunk)
            original_audio_path = temp_audio.name
            temp_audio_path = original_audio_path
        print("original_audio_path", original_audio_path)
        
        # Convert audio to WAV format for STT processing using FFmpeg
        wav_audio_path = None
        try:
            # Get the file extension
            file_ext = os.path.splitext(audio.name)[1].lower().lstrip('.')
            
            # Only convert if not already WAV
            if file_ext != 'wav':
                print(f"Converting {file_ext} to WAV format using FFmpeg")
                
                # Create a new temp file for WAV
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as wav_temp:
                    wav_audio_path = wav_temp.name
                
                # Convert using FFmpeg (same approach as Telegram interface)
                ffmpeg_command = [
                    'ffmpeg', '-y', '-i', original_audio_path, wav_audio_path
                ]
                subprocess.run(ffmpeg_command, check=True)
                
                print(f"Converted audio saved to: {wav_audio_path}")
                
                # Update temp_audio_path to point to WAV file for STT
                temp_audio_path = wav_audio_path
            else:
                print("Audio is already in WAV format")
        except Exception as conv_error:
            print(f"Error converting audio to WAV: {conv_error}")
            # If conversion fails, try to use original file
            pass
        
        # Step 1: Transcribe audio to text using STT
        stt_start = time.time()
        transcribed_text, lang_id, confidence = asyncio.run(generate_with_deepgram_en(temp_audio_path, "nova-3"))
        if lang_id!= 'en':
            transcribed_text = generate_stt(temp_audio_path)
        stt_end = time.time()
        print("transcribed_text", transcribed_text)
        # log_point_to_db(health_metric="api_send_audio", phase="stt_time", latency=stt_end - stt_start, success=bool(transcribed_text))
        
        # if not transcribed_text or transcribed_text == "uncertain_audio_language":
        #     return api.create_response(request, {"error": audio_rerequest_msg}, status=400)
        
        # Step 2: Detect language
        language_code = get_language_langid(transcribed_text)
        print(f"Detected language code: {language_code}")
        
        if language_code not in languages.keys():
            return api.create_response(request, {"error": audio_rerequest_msg}, status=400)
        
        language = languages[language_code]
        english_translated_text = transcribed_text
        
        # Step 3: Translate to English if needed
        if language != "english":
            translation_p1_start = time.time()
            english_translated_text = translate_language(transcribed_text, language, "english", 1)
            translation_p1_end = time.time()
            # log_point_to_db(health_metric="api_send_audio", phase="translation_to_english", 
            #               latency=translation_p1_end - translation_p1_start, success=True)
        
        # Step 4: Process through chatbot pipeline
        langraph_start = time.time()
        response_message = test(english_translated_text, user_id)
        print("response_message", response_message)
        langraph_end = time.time()
        # log_point_to_db(health_metric="api_send_audio", phase="langraph_pipeline", 
        #                latency=langraph_end - langraph_start, success=bool(response_message))
        
        if not response_message:
            return api.create_response(request, {"error": "Failed to generate response"}, status=500)
        
        # Step 5: Check if response is a PDF URL (S3 link for kundli)
        if isinstance(response_message, str) and response_message.startswith("https://astro-ai.s3"):
            return response_message
        
        # Step 6: Summarize if response is too long (>130 words for voice)
        voice_response = response_message
        if len(response_message.split()) > 130:
            summarization_start = time.time()
            system_prompt = f"You are a good summarizer. Please summarize the following text in 130 words while keeping the important details: {response_message}"
            
            # Use litellm for summarization
            model_fallback_list = ["openai/gpt-4o-mini", "gemini/gemini-2.0-flash-exp"]
            for model in model_fallback_list:
                try:
                    summary_response = completion(
                        model=model,
                        messages=[{"content": system_prompt, "role": "user"}]
                    )
                    voice_response = summary_response.choices[0].message.content
                    voice_response = voice_response.replace('*', '').replace('#', '')
                    break
                except Exception as e:
                    print(f"Summarization error with {model}: {e}")
                    continue
            
            summarization_end = time.time()
            # log_point_to_db(health_metric="api_send_audio", phase="summarization", 
            #               latency=summarization_end - summarization_start, success=bool(voice_response))
        
        # Step 7: Translate response back to user's language
        user_language_response = response_message
        user_language_voice_response = voice_response
        
        if language != "english":
            translation_p2_start = time.time()
            user_language_response = translate_language(response_message, "english", language, 2)
            
            # Translate voice response separately if it was summarized
            if voice_response != response_message:
                user_language_voice_response = translate_language(voice_response, "english", language, 3)
            else:
                user_language_voice_response = user_language_response
            
            translation_p2_end = time.time()
            
            # log_point_to_db(health_metric="api_send_audio", phase="translation_from_english", 
            #               latency=translation_p2_end - translation_p2_start, success=True)
        
        # Step 8: Generate TTS audio
        tts_start = time.time()
        audio_file = generate_tts(user_language_voice_response, user_id, language)
        tts_end = time.time()
        # log_point_to_db(health_metric="api_send_audio", phase="tts_generation", 
        #                latency=tts_end - tts_start, success=bool(audio_file))
        
        if not audio_file:
            print("Failed to generate TTS audio, returning text response")
            return {"reply": user_language_response, "audio_url": None}
        
        # Upload audio to S3 and return URL
        try:
            audio_file_path = audio_file
            if os.path.exists(audio_file_path):
                # Generate unique S3 key
                timestamp = int(time.time())
                s3_key = f"audio_responses/{user_id}_{timestamp}.wav"
                
                # Upload to S3
                s3_upload_start = time.time()
                s3.upload_file(
                    audio_file_path,
                    "astro-ai",
                    s3_key,
                    ExtraArgs={"ACL": "public-read", "ContentType": "audio/wav"}
                )
                s3_upload_end = time.time()
                print(f"S3 upload took: {s3_upload_end - s3_upload_start:.2f}s")
                
                # Generate S3 URL
                audio_url = f"https://astro-ai.s3.ap-south-1.amazonaws.com/{s3_key}"
                
                # Clean up local audio file
                os.remove(audio_file_path)
                print(f"Cleaned up TTS audio file: {audio_file_path}")
                print(f"Audio available at: {audio_url}")
                
                # Return response with audio URL and text
                return audio_url
            else:
                print(f"TTS audio file not found: {audio_file_path}")
                return {"reply": user_language_response, "audio_url": None}
                
        except Exception as audio_error:
            print(f"Error uploading audio to S3: {audio_error}")
            return {"reply": user_language_response, "audio_url": None}
            
    except Exception as e:
        print(f"Error in send_audio: {str(e)}")
        log_point_to_db(health_metric="api_send_audio", phase="error", latency=0.0, success=False)
        return api.create_response(request, {"error": str(e)}, status=500)
    
    finally:
        # Clean up temporary audio files
        # Clean up original uploaded file
        if original_audio_path and os.path.exists(original_audio_path):
            try:
                os.remove(original_audio_path)
                print(f"Cleaned up original audio file: {original_audio_path}")
            except Exception as e:
                print(f"Failed to delete original audio file: {e}")
        
        # Clean up converted WAV file (if different from original)
        if temp_audio_path and temp_audio_path != original_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
                print(f"Cleaned up converted WAV file: {temp_audio_path}")
            except Exception as e:
                print(f"Failed to delete converted WAV file: {e}")

@api.post("/onboarding")
def save_onboarding(request, payload: OnboardingRequest):
    """
    Save user onboarding data (name, DOB, birth place, etc.)
    """
    try:
        user_id = clerk_authentication(request)
        
        # Get or create User record for this user_id
        user_profile = UserProfile.objects.get(user_id=user_id)
        
        user, created = User.objects.get_or_create(id=user_profile.user_id)
        
        # Update user_profile JSON field with onboarding data
        user.user_profile = {
            "name": payload.name,
            "dob": payload.dob,
            "time_of_birth": payload.time_of_birth,
            "birth_place": payload.birth_place,
            "gender": payload.gender,
            "client_timezone": payload.client_timezone,

        }
        user.save()
        
        return {
            "success": True,
            "message": "Onboarding data saved successfully",
            "data": user.user_profile
        }
    except UserProfile.DoesNotExist:
        return {"error": "User profile not found"}
    except Exception as e:
        return {"error": str(e)}



@api.get("/history")
def get_history(request, limit: int = 10, offset: int = 0):
    try:
        user_id = clerk_authentication(request)
        
        # Get paginated history for the user
        history = Logger.objects.filter(user_id=user_id).order_by('-created_at')[offset:offset+limit]
        
        # Convert queryset to list of dicts for JSON serialization
        history_list = [
    {
        "id": h.id,
        "user_id": h.user_id,
        "message": h.message,
        "log_type": h.log_type.name,   # ✅ SYSTEM, USER, ERROR
        # OR h.log_type.value if you prefer
        "message_id": h.message_id,
        "created_at": h.created_at,
        "updated_at": h.updated_at,
    }
    for h in history
        ]
        
        return history_list
    except Exception as e:
        return {"error": str(e)}



        


@api.post("/generate-horoscope")
def gener_horoscope(request):
    """
    Generate daily horoscope for the authenticated user
    Returns horoscope predictions based on user's zodiac sign
    """
    try:
        user_id = clerk_authentication(request)
        
        # Get user profile to determine zodiac sign
        user_profile = UserProfile.objects.get(user_id=user_id)
        user = User.objects.filter(id=user_profile.user_id).first()
        
        result = generate_horoscope(user.user_profile, user_id)
        return result
        
    except UserProfile.DoesNotExist:
        return {"error": "User profile not found"}
    except Exception as e:
        return {"error": str(e)}

@api.get("/horoscope")
def get_horoscope(request):
    """
    Get the last generated horoscope for the user
    """
    try:
        user_id = clerk_authentication(request)
        
        user_profile = UserProfile.objects.get(user_id=user_id)
        user = User.objects.filter(id=user_profile.user_id).first()
        
        if not user or not user.horoscope_details:
            return {"error": "No horoscope data found. Please generate horoscope first."}
        
        # Get user name from profile
        name = user.user_profile.get("name", "") if user.user_profile else ""
        
        return {
            "data": {
                "name": name,
                "zodiac_sign": user.horoscope_details.get("zodiac_sign", ""),
                "predictions": user.horoscope_details.get("predictions", {})
            }
        }
        
    except UserProfile.DoesNotExist:
        return {"error": "User profile not found"}
    except Exception as e:
        return {"error": str(e)}



from clerk_backend_api import authenticate_request, AuthenticateRequestOptions, Clerk
from django.conf import settings
# from django.contrib.auth import get_user_model


# User = get_user_model()


def clerk_authentication(request):
        
        if 'Authorization' not in request.headers:
            return {"error": "Authorization header missing"}

        try:
            request_state = authenticate_request(
                request,
                AuthenticateRequestOptions(
                    secret_key=settings.CLERK_API_SECRET_KEY
                )
            )

            if not request_state.is_signed_in:
                print("Authentication failed!", request_state.message)
                return {"error": "User not signed in", "message": request_state.message}
            user_data=''

            with Clerk(bearer_auth=settings.CLERK_API_SECRET_KEY) as clerk:
                user_data = clerk.users.get(user_id=request_state.payload["sub"])
        
                primary_email_address_id = user_data.primary_email_address_id
                email = next(
                    (email for email in user_data.email_addresses if email.id == primary_email_address_id),
                    None
                )
            print(user_data.id)
            print(user_data.username)
            print(email.email_address)
            print(user_data)

            # Check if user already exists
            user, created = UserProfile.objects.get_or_create(
                id=user_data.id,
               email=email.email_address,
               username=user_data.first_name,
            )
            
            # If new user is created, assign auto-incrementing user_id
            if created:
                # Get the maximum user_id from existing records
                max_user_id = UserProfile.objects.aggregate(django_models.Max('user_id'))['user_id__max']
                
                # If no previous records exist, start with 1, otherwise increment
                user.user_id = 1 if max_user_id is None else max_user_id + 1
                user.save()

        except Exception as e:
            print(e)
            return {"error": "Authentication failed", "details": str(e)}

        return user.user_id
