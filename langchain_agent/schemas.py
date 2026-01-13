from pydantic import BaseModel

class ChatRequest(BaseModel):
    user_message: str
    phone_number: str 

class VoiceChatResponse(BaseModel):
    transcription: str
    response: str
    whatsapp: dict


class KundliDetails(BaseModel):
    full_name: str
    gender: str
    day: int
    month: int
    year: int
    place: str
    hour: int
    min: int
    sec: int
    chart_type: str

class KundliRequest(BaseModel):
    details: KundliDetails


class PanchangDetails(BaseModel):
    day: int
    month: int
    year: int
    place: str

class PanchangRequest(BaseModel):
    details: PanchangDetails
class OnboardingRequest(BaseModel):
    name: str
    dob: str  # Format: YYYY-MM-DD
    time_of_birth: str  # Format: HH:MM:00
    birth_place: str
    gender: str
    client_timezone: str