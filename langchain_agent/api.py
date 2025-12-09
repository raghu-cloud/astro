from ninja import NinjaAPI
from .utils import generate_transcription_from_audio, run_llm_pipeline
from .schemas import ChatRequest, VoiceChatResponse, KundliRequest, PanchangRequest
from ninja.files import UploadedFile
import os
import uuid
from whatsapp_interface.utils import send_whatsapp_message
from langchain_agent.pdf_utils.api_utils import handle_generate_kundli, handle_panchang_details

api = NinjaAPI()

@api.post("/chat_text")
def chat(request, payload: ChatRequest):
    response_text = run_llm_pipeline(payload.user_message)
    whatsapp_response = send_whatsapp_message(response_text,payload.phone_number)
    return {"response": response_text, "whatsapp": whatsapp_response}



@api.post("/voice-chat", response=VoiceChatResponse)
def voice_chat(request, file: UploadedFile, phone : str):

    temp_path = f"/tmp/{file.name}"
    with open(temp_path, "wb") as f:
        f.write(file.read())
    
    transcription_text = generate_transcription_from_audio(temp_path)
    
    os.remove(temp_path)
    
    response_text = run_llm_pipeline(transcription_text)
    whatsapp_response = send_whatsapp_message(response_text,phone)
    
    return VoiceChatResponse(transcription=transcription_text, response=response_text, whatsapp=whatsapp_response)


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