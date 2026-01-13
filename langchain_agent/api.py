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
