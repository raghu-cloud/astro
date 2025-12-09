from ..models import AIServiceConfig
# from langchain_community.chat_models import ChatOpenAI
# from langchain_google_genai import ChatGoogleGenerativeAI
# # from langchain_litellm import ChatLiteLLM
# from langchain_community.llms import Anthropic
# from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CHATGROQ_API_KEY = os.getenv("CHATGROQ_API_KEY", "")

# def get_active_llm_config():
#     """
#     Retrieves the active LLM configuration.
#     """
#     return AIServiceConfig.objects.filter(is_active=True).first()

# def get_selected_llm():
#     """
#     Returns the active LLM instance based on the active configuration in the database.
#     If no active model is found, it falls back to default values.
#     """
#     active_config = get_active_llm_config()

#     if not active_config:
#         # Default to OpenAI GPT-4o Mini if no active config is found
#         provider, model_version, temperature = "openai", "gpt-4o-mini", 0.7
#     else:
#         provider = active_config.llm_provider
#         model_version = active_config.llm_model_version or ""
#         temperature = active_config.temperature

#     return get_llm(provider, model_version, temperature)

# def get_llm(provider, model, temperature=0.7):
#     """
#     Returns an instance of the selected LLM provider.
#     """
#     if provider == "openai":
#         # return ChatLiteLLM(openai_api_key=OPENAI_API_KEY, model_name=model, temperature=temperature)
#         return ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name=model, temperature=temperature)
#     elif provider == "gemini":
#         # return ChatLiteLLM(model="gemini/gemini-1.5-pro")
#         return ChatGoogleGenerativeAI(model=model, google_api_key=GEMINI_API_KEY)
#     elif provider == "anthropic":
#         return Anthropic(model=model, anthropic_api_key=ANTHROPIC_API_KEY, temperature=temperature)
#     elif provider == "chatgroq":
#         return ChatGroq(groq_api_key=CHATGROQ_API_KEY, model_name=model, temperature=temperature)
#     else:
#         raise ValueError(f"Unsupported LLM provider: {provider}")