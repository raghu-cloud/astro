from django.db import models

# Create your models here.
from django.core.validators import MinValueValidator, MaxValueValidator

class AIServiceConfig(models.Model):
    # Speech-to-Text (STT) Configuration
    STT_PROVIDERS = [("whisper", "OpenAI Whisper"), ("sarvam_ai", "Sarvam.ai")]
    MODEL_VERSIONS = {
        "whisper": [("whisper-1", "Whisper-1"), ("whisper-large-v2", "Whisper-Large-V2"), ("whisper-large-v3", "Whisper-Large-V3")],
        "sarvam_ai": [("saarika:v2", "Saarika:V2")],
    }

    stt_provider = models.CharField(max_length=50, choices=STT_PROVIDERS, blank=True, null=True)
    stt_model_version = models.CharField(max_length=50, blank=True, null=True)

    # Translation Configuration
    TRANSLATION_PROVIDERS = [("sarvam_ai", "Sarvam.ai")]
    TRANSLATION_MODEL_VERSIONS = {"sarvam_ai": [("mayura:v1", "Mayura:V1")]}

    translation_provider = models.CharField(max_length=50, choices=TRANSLATION_PROVIDERS, blank=True, null=True)
    translation_model_version = models.CharField(max_length=50, blank=True, null=True)

    # Text-to-Speech (TTS) Configuration
    TTS_PROVIDERS = [("parler_tts", "IndicParler TTS"), ("smallest_ai", "Smallest.ai"), ("sarvam_ai", "Sarvam.ai")]
    
    TTS_MODEL_VERSIONS = {
        "parler_tts": [],
        "smallest_ai": [("lightning", "Lightning"), ("lightning-large", "Lightning Large")],
        "sarvam_ai": [("bulbul:v1", "Bulbul:V1")],
    }

    VOICES = {
        "parler_tts": [("Divya", "Divya"), ("Anjali", "Anjali"), ("Rohit", "Rohit")],
        "smallest_ai": [("chetan", "Chetan"), ("arnav", "Arnav"), ("abhinav", "Abhinav"), ("sushma", "Sushma")],
        "sarvam_ai": [("meera", "Meera"), ("maitreyi", "Maitreyi"), ("arvind", "Arvind"), ("arjun", "Arjun")],
    }

    tts_provider = models.CharField(max_length=50, choices=TTS_PROVIDERS, blank=True, null=True)
    tts_model_version = models.CharField(max_length=50, blank=True, null=True)
    tts_voice = models.CharField(max_length=50, blank=True, null=True)

    # LLM Configuration
    LLM_PROVIDERS = [("openai", "OpenAI"), ("gemini", "Google Gemini"), ("anthropic", "Anthropic Claude"), ("chatgroq", "ChatGroq")]
    LLM_MODEL_VERSIONS = {
        "openai": [("gpt-4o", "GPT-4o"), ("gpt-4o-mini", "GPT-4o Mini"), ("gpt-4-turbo", "GPT-4 Turbo")],
        "gemini": [("gemini-1.5-flash", "Gemini 1.5 Flash"), ("gemini-1.5-pro", "Gemini 1.5 Pro")],
        "anthropic": [("claude-3-sonnet", "Claude 3 Sonnet"), ("claude-3-haiku", "Claude 3 Haiku")],
    }

    llm_provider = models.CharField(max_length=50, choices=LLM_PROVIDERS, blank=True, null=True)
    llm_model_version = models.CharField(max_length=50, blank=True, null=True)

    # Common Settings
    temperature = models.FloatField(default=0.7, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AI Config - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')} - Active: {self.is_active}"
    

    def get_stt_model_version_label(self):
        return dict(self.MODEL_VERSIONS.get(self.stt_provider, [])).get(self.stt_model_version, self.stt_model_version)

    def get_translation_model_version_label(self):
        return dict(self.TRANSLATION_MODEL_VERSIONS.get(self.translation_provider, [])).get(self.translation_model_version, self.translation_model_version)

    def get_tts_model_version_label(self):
        return dict(self.TTS_MODEL_VERSIONS.get(self.tts_provider, [])).get(self.tts_model_version, self.tts_model_version)

    def get_tts_voice_label(self):
        return dict(self.VOICES.get(self.tts_provider, [])).get(self.tts_voice, self.tts_voice)

    def get_llm_model_version_label(self):
        return dict(self.LLM_MODEL_VERSIONS.get(self.llm_provider, [])).get(self.llm_model_version, self.llm_model_version)
    
    class Meta:
        verbose_name = "AI Service Configuration"
        verbose_name_plural = "AI Service Configurations"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "stt_provider", "stt_model_version",
                    "translation_provider", "translation_model_version",
                    "tts_provider", "tts_model_version", "tts_voice",
                    "llm_provider", "llm_model_version",
                    "temperature"
                ],
                name="unique_ai_service_config"
            )
        ]
