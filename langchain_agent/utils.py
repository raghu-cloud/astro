import os
import re
import json
import logging
import requests
import subprocess
import asyncio
import aiohttp
import time
import threading
# from psycopg_pool import ConnectionPool
import ast
from django.db import connection
import io
from pydantic import BaseModel
from datetime import datetime
import base64
import litellm
from io import BytesIO
from dotenv import load_dotenv
from typing import Annotated
from litellm import completion, completion_cost,token_counter
from typing_extensions import TypedDict
import concurrent.futures
import requests
from prompts import INTENT_NODE_PROMPT,CONVERSATION_PROMPT,KUNDLI_MISSING_DETAILS_PROMPT,KUNDLI_ASK_DETAILS_PROMPT,STORE_IN_DB_PROMPT,HOROSCOPE_MISSING_DETAILS_PROMPT,HOROSCOPE_ASK_DETAILS_PROMPT
from datetime import datetime
from django.conf import settings
from timing_test_csv_utils import log_time_to_csv
from django.db import close_old_connections
import boto3
import json
from langchain.memory import ConversationBufferMemory
from langchain_agent.models import User,Logger,store_detail
from langchain_agent.models import LogType
# from geopy.geocoders import Nominatim
from psycopg_pool import ConnectionPool
import telegram_interface.utils
from whatsapp_interface.utils import upload_pdf, send_pdf
from gtts import gTTS
import boto3
from openai import OpenAI
from langchain_agent.pdf_utils.generate_pdf import call_divine,call_horoscope
import influxdb_client_3
from influxdb_client_3 import InfluxDBClient3, Point, WriteOptions
from influx import log_point_to_db
from langchain_agent.models import LogType




# Register a TrueType font with ReportLab

load_dotenv()

DB_URI = os.getenv('DB_URI')
connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

astro_conn=os.getenv('ASTRO_CONN')


model_fallback_list = ["openai/gpt-4o-mini","gemini/gemini-2.0-flash","gemini/gemini-2.0-flash-lite"]


s3 = boto3.client("s3",aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))


logger = logging.getLogger(__name__)

pdf_sent_flag = 0

llm_provider = os.getenv("LLM_PROVIDER", "openai")
model_name = os.getenv("MODEL_NAME", "gpt-4o")
openai_api_key = os.getenv("OPENAI_API_KEY")
divine_api_token = os.getenv("DIVINE_API_TOKEN")
divine_api_key = os.getenv("DIVINE_API_KEY")
roxy_api_key = os.getenv("ROXY_API")
# client = OpenAI(api_key=openai_api_key)
anthropic_api_key =os.getenv('ANTHROPIC_API_KEY')
gemini_api_key = os.getenv("GEMINI_API_KEY")
chatgroq_api_key = os.getenv("GROQ_API_KEY")



user_memory = {}


def get_user_memory(chat_id):
    """Get or create a memory instance for a specific user."""
    if chat_id not in user_memory:
        user_memory[chat_id] = ConversationBufferMemory(
            memory_key="chat_history", input_key="user_message", return_messages=True
        )
    return user_memory[chat_id]


user_pdf_flags = {}


def get_user_pdf_flag(chat_id):
    """Get or create a PDF flag for a specific user."""
    if chat_id not in user_pdf_flags:
        user_pdf_flags[chat_id] = 0  # Initialize flag to 0 (not sent)
    return user_pdf_flags[chat_id]


def set_user_pdf_flag(chat_id, value):
    """Set the PDF flag for a specific user."""
    user_pdf_flags[chat_id] = value


def preprocess_input(user_message):
    """Cleans input text and prepares it for LLM processing."""
    user_message = user_message.strip()
    user_message = re.sub(r"\s+", " ", user_message)
    return user_message


memory = ConversationBufferMemory(
    memory_key="chat_history", input_key="user_message", return_messages=True
)


def store_horoscope_in_db(data, user_id):
    user = User.objects.get(id=user_id)
    user.horoscope_details = data[0]["data"]
    user.save()


def call_litellm(system_prompt):
    model_write=''
    for model in model_fallback_list:
        model_write=model
        try:
            response = completion(
  model=model,
  messages=[{ "content": system_prompt,"role": "user"}]

) 
            
            break
        except Exception as e:
            logger.error(f"error occurred: {e}")
    cost = completion_cost(completion_response=response)
    tokens=token_counter( model=model,
  messages=[{ "content": system_prompt,"role": "user"}])

    content=response.choices[0].message.content
    content=content.replace('*','')
    content=content.replace('#','')
    model_name=model_write.split('/')[0]
    model_version=model_write.split('/')[1]

    
    return content,model_name,model_version,tokens,cost


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CHATGROQ_API_KEY = os.getenv("CHATGROQ_API_KEY", "")


def store_in_db_node(chat_id,message,message_id,message_type):
    """
    Processes and stores structured user data in the database using an LLM, 
    based on the most recent user and bot messages.

    Workflow:
    - Fetches the latest user and bot messages for the given chat_id.
    - Formats a system prompt (`STORE_IN_DB_PROMPT`) with these messages.
    - Sends the prompt to an LLM via `call_litellm` and parses the returned JSON.
    - Updates or inserts user profile data into the database under a specific category (field) if it exists on the `User` model.

    Parameters:
    - chat_id (int): Unique identifier of the user/chat session.
    - message (str): Message to return after processing (e.g., confirmation or content to be sent back).
    - message_id (str): Unique identifier of the current message in conversation.
    - message_type (str): Type of the message (e.g., "text", "image", etc.)

    Returns:
    - str: The original message if successful, or "error" in case of failure.

    Logs:
    - Timing and performance metrics at different stages (`llm_time`, `store_in_db_time`, `total_time`) using `log_point_to_db`.
    - Errors and completion status to the logger.

    Notes:
    - Assumes `store_detail`, `User`, `call_litellm`, `log_point_to_db`, and `STORE_IN_DB_PROMPT` are defined in the scope.
    - Handles creation and updating of user attributes (e.g., personal details, preferences) dynamically using the category name.
    - Handles edge cases where no prior bot message exists.
    """
    try:
    
        start_total = time.time()
      
        latest_bot_message=''
       
        latest_user_message = store_detail.objects.filter(metric="user_message", user_id=chat_id).latest('id').message_text
        latest_bot_message_obj = store_detail.objects.filter(
    metric="bot_message",
    user_id=chat_id
).order_by('-id').first()

        latest_bot_message = latest_bot_message_obj.message_text if latest_bot_message_obj else ""

        

        today_date = datetime.today().strftime("%Y-%m-%d")
        system_prompt = STORE_IN_DB_PROMPT.format(latest_user_message=latest_user_message,latest_bot_message=latest_bot_message)



        llm_start = time.time()
        content,model_name,model_version,tokens,cost=call_litellm(system_prompt)
        llm_end = time.time()
       
        log_point_to_db(health_metric="store_in_db_node", phase="llm_time", latency= llm_end - llm_start, model=model_name, model_version= model_version,tokens=tokens,cost=cost,success= True)
        extracted_text = content.replace("```json", "").replace("```", "").strip()


        extracted_data = json.loads(extracted_text)
 


        db_start_time=time.time()
        try:

            
           
            
            for data in extracted_data:
         
                if data:
                    category = data.get("category") 
                    del data['category']
 
                    
                    if category and hasattr(User, category):
                
                        profile, created = User.objects.get_or_create(
                            id=chat_id, 
                            defaults={category: data}
                        )
                        
                        if not created:
                            existing_data = getattr(profile, category) or {}
                            existing_data.update(data)  # More efficient than looping
                            setattr(profile, category, existing_data)
                            profile.save()
        finally:
            logger.info("completed")  # Explicitly close connection
        db_end_time=time.time()
       
        log_point_to_db(health_metric="store_in_db_node", phase="store_in_db_time", latency= db_end_time - db_start_time, success= True)
        
        end_total = time.time()
      
        log_point_to_db(health_metric="store_in_db_node", phase="total_time", latency= end_total - start_total, success= True)
    
        return message
   
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        log_point_to_db(health_metric="store_in_db_node", phase="error", latency=0,success= False)
        return "error"
    finally:
        logger.info("completed")

def intent_node(message,chat_id,message_id,message_type):
    """
    Determines the user's intent from the given message and routes the conversation accordingly.

    This function:
    - Checks the user's current horoscope-related flow (daily, weekly, or kundli).
        - If already in a specific flow, directly delegates to `decision_node` with the corresponding intent.
    - Identifies whether kundli details are present for context.
    - Builds a system prompt with the user message and kundli presence status.
    - Uses a language mod
    \el (`call_litellm`) to predict the user's intent from the message.
    - Stores the model's prediction in the database.
    - Logs metrics including latency, model version, tokens used, and cost.
    - Finally, routes the flow to `decision_node` with the predicted intent.

    Parameters:
    - message (str): The latest message from the user.
    - chat_id (int): Unique identifier of the user/chat session.
    - message_id (int): Identifier of the current message for tracking.
    - message_type (str): Type of message (e.g., "text", "voice").

    Returns:
    - Response from `decision_node()` based on either the detected intent or fallback value ("error" in case of failure).
    """


    try:
        start_total = time.time()
        
        # latest_message = store_detail.objects.filter(metric="user_message", user_id=chat_id).latest('id').message_text
#         latest_bot_message_obj = store_detail.objects.filter(
#     metric="bot_message",
#     user_id=chat_id
# ).order_by('-id').first()

#         latest_bot_message = latest_bot_message_obj.message_text if latest_bot_message_obj else ""


        user=User.objects.get(id=chat_id)
        if user.daily_horoscope_flow==True:
            end_total = time.time()
            log_point_to_db(health_metric="intent_node", phase="total_time", latency=end_total - start_total, success= True)
            return decision_node(chat_id,'daily horoscope',message_id,message_type)
        if user.weekly_horoscope_flow==True:
            end_total = time.time()
            log_point_to_db(health_metric="intent_node", phase="total_time", latency=end_total - start_total, success= True)
            return decision_node(chat_id,'weekly horoscope',message_id,message_type)
        if user.kundli_flow==True:
            end_total = time.time()
            log_point_to_db(health_metric="intent_node", phase="total_time", latency=end_total - start_total, success= True)
            return decision_node(chat_id,'kundli',message_id,message_type)

        kundli_present='absent'
        if len(user.kundli_details)>0:
            kundli_present='present'

        system_prompt = INTENT_NODE_PROMPT.format(last_content=message,kundli_present=kundli_present)
        start_llm = time.time()
        content,model_name,model_version,tokens,cost=call_litellm(system_prompt)
        end_llm = time.time()
        log_point_to_db(health_metric="intent_node", phase="llm_time", latency=end_llm - start_llm, model=model_name,tokens=tokens,cost=cost, model_version= model_version, success= True)

        store = store_detail.objects.create(
    message_text=content,
    user_id=chat_id,
    metric="decision_node",message_id=message_id,message_type=message_type
)
        store.save()
        end_total = time.time()
        log_point_to_db(health_metric="intent_node", phase="total_time", latency=end_total - start_total, success= True)
        return decision_node(chat_id,content,message_id,message_type)
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        log_point_to_db(health_metric="intent_node", phase="error", latency=0,success= False)
        return decision_node(chat_id,"error",message_id,message_type)
    finally:
        logger.info("completed")






def decision_node(chat_id,content,message_id,message_type):
    """
    Routes the user interaction to the appropriate node based on the interpreted intent/content.

    This function:
    - Retrieves the user profile using the chat ID.
    - Analyzes the `content` (intent string) to decide which flow to activate:
        - If "conversation" is detected → routes to `conversation_node`.
        - If "kundli"/"kundali" is detected → sets `kundli_flow` and routes to `kundli_node`.
        - If "vector_db" is detected → routes to `q_and_a_kundli_node`.
        - If "horoscope" is detected:
            - If it includes "daily horoscope", activates `daily_horoscope_flow`.
            - If it includes "weekly horoscope", activates `weekly_horoscope_flow`.
            - Routes to `horoscope_node`.

    Additionally:
    - Tracks and logs total execution time for monitoring.
    - In case of errors, defaults to routing the user to `horoscope_node` with "error" content.

    Parameters:
    - chat_id (int): Unique user/chat identifier.
    - content (str): Intent string (typically generated by a language model).
    - message_id (int): Message identifier for tracking.
    - message_type (str): Type of the message (e.g., "text", "voice").

    Returns:
    - The result of the called node function corresponding to the identified intent.
    """
    try:
    
        start_total = time.time()
        user=User.objects.get(id=chat_id)

        if  "conversation" in content:
            end_total = time.time()
            log_point_to_db(health_metric="decision_node", phase="total_time", latency=end_total - start_total, success= True) 
            return conversation_node(chat_id,message_id,message_type)
        elif content=='kundli' or content=='kundali' or content=='kundali\n' or content=='kundli\n' or 'kundli' in content:
            end_total = time.time()
            user.kundli_flow=True
            user.save()
            log_point_to_db(health_metric="decision_node", phase="total_time", latency=end_total - start_total, success= True)
            return kundli_node(chat_id,message_id,message_type)
        elif "vector_db" in content:
            end_total = time.time()
            log_point_to_db(health_metric="decision_node", phase="total_time", latency=end_total - start_total, success= True)
            return q_and_a_kundli_node(chat_id,message_id,message_type)

        elif  "horoscope" in content :   
            if 'daily horoscope' in content:
                user.daily_horoscope_flow=True
                user.save()
            if 'weekly horoscope' in content:
                user.weekly_horoscope_flow=True
                user.save()
            end_total = time.time()
            log_point_to_db(health_metric="decision_node", phase="total_time", latency=end_total - start_total, success= True)
            return horoscope_node(chat_id,content,message_id,message_type)
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        log_point_to_db(health_metric="decision_node", phase="error", latency=0,success= False)
        return horoscope_node(chat_id,"error",message_id,message_type)
    finally:
        logger.info("completed")

# def get_lat_lon_photon(place):
#     """
#     Retrieves the latitude and longitude for a given place name using the Photon geocoding API.

#     This function sends a GET request to the Photon API with the place query and parses
#     the response to extract geographic coordinates.

#     Parameters:
#     - place (str): The name of the location to geocode (e.g., city, address, landmark).

#     Returns:
#     - (lat, lon) (tuple of str or None): 
#         - A tuple containing the latitude and longitude as strings if found.
#         - Returns (None, None) if no coordinates are found or an error occurs.

#     Notes:
#     - Uses the first match returned by the Photon API.
#     - Logs any exceptions and returns (None, None) in case of failure.
#     """
#     try:
#         url = "https://photon.komoot.io/api/"
#         params = {
#             "q": place
#         }
#         response = requests.get(url, params=params)
#         data = response.json()

#         if data['features']:
#             lon, lat = data['features'][0]['geometry']['coordinates']
#             return str(lat), str(lon)
#         else:
#             return None, None
#     except Exception as e:
#         logger.error(f"Error occurred: {e}")
#         return None, None
#     finally:
#         logger.info("completed")

def get_lat_lon_nomatim(place):
    """
    Retrieves latitude and longitude for a given place using Nominatim (OpenStreetMap).

    Parameters:
    - place (str): Location name

    Returns:
    - (lat, lon): tuple of strings or (None, None)
    """
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": place,
            "format": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "endee-testing-platform/1.0"
        }

        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data:
            return data[0]["lat"], data[0]["lon"]

        return None, None

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return None, None

    finally:
        logger.info("completed")




def kundli_node(chat_id,message_id,message_type):
    """
    Handles the flow for generating a personalized Kundli based on the user's chat context.

    This function:
    - Retrieves the user's latest message and last bot response.
    - Constructs a system prompt using the user's profile and prior messages.
    - Sends the prompt to a language model to extract Kundli-relevant details (like date, time, place).
    - If all required details are available, it triggers the Kundli generation process.
    - If details are missing, it uses a fallback model to ask for those.
    - Logs timing, cost, and token usage for observability.
    - Stores responses and intermediate outputs in the database.

    Parameters:
    - chat_id (int): Unique identifier for the user/chat session.
    - message_id (int): ID of the current message being processed.
    - message_type (str): Type of message (e.g., "text", "image", etc.).

    Returns:
    - A result from `call_divine()` if all Kundli details are gathered.
    - Otherwise, a message asking for more details is stored and returned via `store_in_db_node()`.
    - In case of failure, logs the error and stores a fallback error response.
    """
    try:
   
        start_total = time.time()
        latest_message = store_detail.objects.filter(metric="user_message", user_id=chat_id).latest('id').message_text
        latest_bot_message_obj = store_detail.objects.filter(
    metric="bot_message",
    user_id=chat_id
).order_by('-id').first()

        latest_bot_message = latest_bot_message_obj.message_text if latest_bot_message_obj else ""
        
        user = User.objects.get(id=chat_id)
        pre_llm_start = time.time()
        system_prompt=KUNDLI_MISSING_DETAILS_PROMPT.format(last_message=latest_bot_message,last_user_message=latest_message,user_profile=user.user_profile,Kundli=Kundli)
        pre_llm_end = time.time()
        llm_start_kundli = time.time()
        model_write=''
        for model in model_fallback_list:
            model_write=model
            try:
                response = completion(
        model=model,
        response_format=Kundli,
    messages=[{ "content": system_prompt,"role": "user"}]
    )
                break
            except Exception as e:
                logger.error(f"error occurred: {e}")
    
        model_name=model_write.split('/')[0]
        model_version=model_write.split('/')[1]
        cost = completion_cost(completion_response=response)
        tokens=token_counter( model=model_write,
        messages=[{ "content": system_prompt,"role": "user"}])
        llm_end_kundli = time.time()
     
        log_point_to_db(health_metric="kundli_node", phase="llm_ask_missing_details_time", latency= llm_end_kundli - llm_start_kundli, model=model_name, model_version= model_version,tokens=tokens,cost=cost, success= True)

        content=response.choices[0].message.content
        extracted_text = content.replace("```json", "").replace("```", "").strip()
        details = {}
        try:
            details = json.loads(extracted_text)
        except Exception as e:
            logger.error(f"An error occurred: {e}")

        if len(details["place"]) > 0:
            details['lat'], details['lon'] = get_lat_lon_nomatim(details["place"])
        print(details)


        if all(len(v) > 0 for v in details.values()):
            print("hello")

            # telegram_interface.utils.send_text_message(chat_id,"We are generating your personalised Kundli, Please wait for a minute or two....")

            end_total = time.time()
            log_point_to_db(health_metric="kundli_node", phase="total_time", latency=end_total - start_total, success= True)
            return call_divine(details,chat_id,message_id,message_type)

        system_prompt=KUNDLI_ASK_DETAILS_PROMPT.format(last_user_message=latest_message,details=details)        
        llm_missing_details_start = time.time()
        content,model_name,model_version,tokens,cost=call_litellm(system_prompt)
        llm_missing_details_end = time.time()
        log_point_to_db(health_metric="kundli_node", phase="llm_ask_missing_details_time", latency= llm_missing_details_end - llm_missing_details_start, model=model_name, model_version= model_version, tokens=tokens,cost=cost,success= True)
        store = store_detail.objects.create(
    message_text=content,
    user_id=chat_id,
    metric="kundli_node",message_id=message_id,message_type=message_type
)
        store.save()
        end_total = time.time()
        log_point_to_db(health_metric="kundli_node", phase="total_time", latency= end_total - start_total, success= True)
        return store_in_db_node(chat_id,content,message_id,message_type)
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        log_point_to_db(health_metric="kundli_node", phase="error", latency=0,success= False)
        return store_in_db_node(chat_id,"error",message_id,message_type)
    finally:
        logger.info("completed")





def find_present_yogas(yoga_data):
    """
    Identifies present yogas from the nested dictionary structure.

    Args:
        yoga_data (dict): The dictionary containing yoga information,
                          expected to have a 'data' key.

    Returns:
        list: A list of names of the yogas where 'is_valid' is 'true'.
    """
    try:
        present_yogas_list = []
        # Safely access the main 'data' dictionary
        main_data = yoga_data.get("data", {})

        # Iterate through the top-level items (potential yogas or groups)
        for key, value in main_data.items():
            # Check if the item itself is a yoga definition (has 'is_valid')
            if isinstance(value, dict) and "is_valid" in value:
                if value.get("is_valid") == "true":
                    # Add the name, fallback to the key if name is missing
                    present_yogas_list.append(value.get("name", key))
            # Check if the item is a dictionary (potentially a group of yogas)
            elif isinstance(value, dict):
                # Iterate through the items within this potential group
                for sub_key, sub_value in value.items():
                    # Check if the sub-item is a yoga definitionLLM
                    if isinstance(sub_value, dict) and "is_valid" in sub_value:
                        if sub_value.get("is_valid") == "true":
                            # Add the name, fallback to the sub_key if name is missing
                            present_yogas_list.append(sub_value.get("name", sub_key))

        return present_yogas_list
    except Exception as e:
        logger.error(f"Error {e}")


def parse_date(date_str):
    """Parse date string into datetime object"""
    return datetime.strptime(date_str, '%Y-%m-%d') if date_str != '--' else None

def find_current_dasha(data, today):
    """
    Determines the current Maha Dasha, Antar Dasha, and Pratyantar Dasha 
    for a given date from Vedic astrology dasha data.

    Parameters:
    - data (dict): A nested dictionary representing dasha periods with the following structure:
        {
            "maha_dasha": {
                "MahaName1": {
                    "start_date": "YYYY-MM-DD",
                    "end_date": "YYYY-MM-DD",
                    "antar_dasha": {
                        "AntarName1": {
                            "start_time": "YYYY-MM-DD",
                            "end_time": "YYYY-MM-DD",
                            "pratyantar_dasha": {
                                "PratyantarName1": {
                                    "start_time": "YYYY-MM-DD",
                                    "end_time": "YYYY-MM-DD"
                                },
                                ...
                            }
                        },
                        ...
                    }
                },
                ...
            }
        }

    - today (datetime.date): The date for which to find the current dasha status.

    Returns:
    - tuple:
        (start_maha, end_maha, start_antar, end_antar, start_pratyantar, end_pratyantar) 
        where each item is a `datetime.date` representing the start or end of a dasha period.

    - str:
        A message indicating that a Maha, Antar, or Pratyantar Dasha could not be found for the given date.

    Exceptions:
    - Catches and logs all exceptions and returns nothing (implicit `None`) on failure.
    """

    # Find current Maha Dasha
    try:
        current_maha = None
        for maha_name, maha_data in data['maha_dasha'].items():
            start = parse_date(maha_data['start_date'])
            end = parse_date(maha_data['end_date'])
            if start <= today <= end:
                current_maha = (maha_name, maha_data)
                start_maha=start
                end_maha=end
                break
        
        if not current_maha:
            return "No current Maha Dasha found"
        
        # Find current Antar Dasha
        maha_name, maha_data = current_maha
        current_antar = None
        for antar_name, antar_data in maha_data['antar_dasha'].items():
            start = parse_date(antar_data['start_time'])
            end = parse_date(antar_data['end_time'])
            if start and end and start <= today <= end:
                current_antar = (antar_name, antar_data)
                start_antar=start
                end_antar=end
                break
        
        if not current_antar:
            return f"Current Maha Dasha: {maha_name} (No Antar Dasha found)"
        
        # Find current Pratyantar Dasha
        antar_name, antar_data = current_antar
        current_pratyantar = None
        for pratyantar_name, pratyantar_data in antar_data['pratyantar_dasha'].items():
            start = parse_date(pratyantar_data['start_time'])
            end = parse_date(pratyantar_data['end_time'])
            if start and end and start <= today <= end:
                current_pratyantar = pratyantar_name
                start_pratyantar=start
                end_pratyantar=end
                break
        
        if not current_pratyantar:
            return f"Current: {maha_name} - {antar_name} (No Pratyantar Dasha found)"
        
        return (start_maha,end_maha,start_antar,end_antar,start_pratyantar,end_pratyantar)
    except Exception as e:
        logger.error(f"Error {e}")


def q_and_a_kundli_node(chat_id,message_id,message_type):

    try:
        start_total = time.time()
        
        query_text = store_detail.objects.filter(metric="user_message", user_id=chat_id).latest('id').message_text
        latest_bot_message_obj = store_detail.objects.filter(
    metric="bot_message",
    user_id=chat_id
).order_by('-id').first()

        latest_bot_message = latest_bot_message_obj.message_text if latest_bot_message_obj else ""

        user=User.objects.get(id=chat_id)
        today_date = str(datetime.today().strftime("%Y-%m-%d"))
        basic_astro_details=user.basic_astro_details
        manglik_dosha=user.manglik_dosha
        sade_sathi=user.sadhe_sati
        kaal_sarpa=user.kaal_sarpa_yoga
        all_yogas=user.yogas
        ghata_chakra=user.ghata_chakra
        vimshottari_dasha=user.vimshottari_dasha
        today=datetime.today()

        user_details=user.user_profile
        maha_dasha=user.mahadasha_analysis
        # gender=user.gen
        pratyantar_dasha=user.pratyantardasha_analysis
        antar_dasha=user.antardasha_analysis
        ascendant_report=user.ascendant_report
        planetary_posistion=user.planetary_positions
        planets=[]
        for planet in planetary_posistion['data']['planets']:
            data={}
            data['name']=planet['name']

            data['sign']=planet['sign']
        
            data['house']=planet['house']
            data['nakshatra']=planet['nakshatra']
            data['degree']=planet['full_degree']
            data['nakshatra_lord']=planet['nakshatra_lord']
            data['retrograde']=planet['is_retro']
            data['combust']=planet['is_combusted']
            data['karakamsha']=planet['karakamsha']
            data['nakshatra_pada']=planet['nakshatra_pada']
            data['rashi_lord']=planet['rashi_lord']
            data['awastha']=planet['awastha']
            data['karakamsha']=planet['karakamsha']
    
            
        
            planets.append(data)
        
        dates=find_current_dasha(vimshottari_dasha['data'],today)

        # user_name=user_details['name']
        # print(basic_astro_details)
        user_name=basic_astro_details['data']['full_name']
        user_dob=basic_astro_details['data']['date']
        gender=basic_astro_details['data']['gender']
        user_tob=basic_astro_details['data']['hour']
        place=basic_astro_details['data']['place']
        latitude=basic_astro_details['data']['latitude']
        longitude=basic_astro_details['data']['longitude']
        sunrise=basic_astro_details['data']['sunrise']
        sunset=basic_astro_details['data']['sunset']
        timezone=basic_astro_details['data']['timezone']
        tithi = basic_astro_details['data']['tithi']
        paksha = basic_astro_details['data']['paksha']
        vaara = basic_astro_details['data']['vaar']
        sunsign = basic_astro_details['data']['sunsign']
        moonsign = basic_astro_details['data']['moonsign']  
        gana = basic_astro_details['data']['gana']
        nadi = basic_astro_details['data']['nadi']
        yoni = basic_astro_details['data']['yoni']
        nakshatra= basic_astro_details['data']['nakshatra']
        manglik_present=manglik_dosha['data']['manglik_dosha']
        manglik_strength=manglik_dosha['data']['strength']
        sade_sathi_result = sade_sathi.get('data', {}).get('sadhesati', {}).get('result')
        kaal_sarpa_yoga_result=kaal_sarpa['data']['result']
        ascendant_report_sign=ascendant_report['data']['ascendant']
        ascendatn_report_planetary_lord=ascendant_report['data']['planetary_lord']
        yoga=ghata_chakra['data']['yoga']
        karana=ghata_chakra['data']['karana']



        current_maha_dasha=maha_dasha['data']['maha_dasha']
        current_antar_dasha=antar_dasha['data']['antar_dasha']
        current_pratyantar_dasha=pratyantar_dasha['data']['pratyantar_dasha']
        present_yogas = find_present_yogas(all_yogas)
        

    
        query_text=f'Based on todays date {today_date}'+query_text
        system_prompt=f'''You are "JyotishAI", an advanced AI assistant specializing in Vedic Astrology (Jyotish). Your primary purpose is to provide personalized astrological insights, guidance, and interpretations based *strictly* on the user's provided Kundli (Vedic birth chart) details. You should act as a knowledgeable, empathetic, and ethical astrological guide. Your goal is to help the user understand their potential, challenges, and the cosmic influences acting upon their life, empowering them to make informed decisions. You interpret astrological configurations, planetary periods (Dashas), transits, and yogas according to established Vedic principles (primarily Parashari, using Vimshottari Dasha).
        ## 2. User Profile

    * **User Name:** {user_name}
    * **Gender:** {gender}


    ## 3. User's Kundli Details (Vedic Astrology)

    This is the foundational data for all your interpretations. Refer *exclusively* to this data for astrological analysis.

    * **Birth Details:**
        * Date of Birth (DOB): {user_dob} 
        * Time of Birth (TOB): {user_tob} 
        * Place of Birth (POB): {place}, 
        * Coordinates: Latitude {latitude}, Longitude {longitude}
        * Timezone at Birth: {timezone}
        * Sunrise (Birth Date): {sunrise}
        * Sunset (Birth Date): {sunset}
    * **Panchanga Details :**
        * Tithi: {tithi} 
        * Paksha: {paksha} 
        * Vaar (Weekday): {vaara} 
        * Nakshatra (Birth Star): {nakshatra} 
        * Yoga: {yoga}
        * Karana: {karana}
    * **Core Chart Details:**
        * Ayanamsa Used: KP 
        * Ascendant (Lagna): {ascendant_report_sign} 
        * Ascendant Lord: {ascendatn_report_planetary_lord} 
        * Moon Sign (Chandra Rashi): {moonsign} 
        * Sun Sign (Surya Rashi): {sunsign} 
        * Nakshatra-Based Temperament: Gana {gana} , Nadi {nadi} , Yoni {yoni} 
    * **Planetary Positions (Graha Sthiti):
        * **{planets[0]['name']} 

            * Sign: {planets[0]['sign']} 
            * House: {planets[0]['house']} 
            * Degree: {planets[0]['degree']} 
            * Nakshatra: {planets[0]['nakshatra']}, Pada: {planets[0]['nakshatra_pada']}, Nakshatra Lord: {planets[0]['nakshatra_lord']}
            * Retrograde: {planets[0]['retrograde']}
            * Combust: {planets[0]['combust']} 
            * House Lordship: Lord of House(s) {planets[0]['rashi_lord']} 
        
            * Awastha (State): {planets[0]['awastha']}
            * Karakamsha Role: {planets[0]['karakamsha']} 
            * **{planets[1]['name']} 

            * Sign: {planets[1]['sign']} 
            * House: {planets[1]['house']} 
            * Degree: {planets[1]['degree']} 
            * Nakshatra: {planets[1]['nakshatra']}, Pada: {planets[1]['nakshatra_pada']}, Nakshatra Lord: {planets[1]['nakshatra_lord']}
            * Retrograde: {planets[1]['retrograde']}
            * Combust: {planets[1]['combust']} 
            * House Lordship: Lord of House(s) {planets[1]['rashi_lord']} 
    
            * Awastha (State): {planets[1]['awastha']} 
            * Karakamsha Role: {planets[1]['karakamsha']} 
            * **{planets[2]['name']} 

            * Sign: {planets[2]['sign']} 
            * House: {planets[2]['house']} 
            * Degree: {planets[2]['degree']} 
            * Nakshatra: {planets[2]['nakshatra']}, Pada: {planets[2]['nakshatra_pada']}, Nakshatra Lord: {planets[2]['nakshatra_lord']}
            * Retrograde: {planets[2]['retrograde']}
            * Combust: {planets[2]['combust']} 
            * House Lordship: Lord of House(s) {planets[2]['rashi_lord']} 
        
            * Awastha (State): {planets[2]['awastha']} 
            * Karakamsha Role: {planets[2]['karakamsha']} 
            * **{planets[3]['name']} 

            * Sign: {planets[3]['sign']} 
            * House: {planets[3]['house']} 
            * Degree: {planets[3]['degree']} 
            * Nakshatra: {planets[3]['nakshatra']}, Pada: {planets[3]['nakshatra_pada']}, Nakshatra Lord: {planets[3]['nakshatra_lord']}
            * Retrograde: {planets[3]['retrograde']} 
            * Combust: {planets[3]['combust']} 
            * House Lordship: Lord of House(s) {planets[3]['rashi_lord']} 

            * Awastha (State): {planets[3]['awastha']} 
            * Karakamsha Role: {planets[3]['karakamsha']} 
            * **{planets[4]['name']} 

            * Sign: {planets[4]['sign']} 
            * House: {planets[4]['house']} 
            * Degree: {planets[4]['degree']} 
            * Nakshatra: {planets[4]['nakshatra']}, Pada: {planets[4]['nakshatra_pada']}, Nakshatra Lord: {planets[4]['nakshatra_lord']}
            * Retrograde: {planets[4]['retrograde']} 
            * Combust: {planets[4]['combust']} 
            * House Lordship: Lord of House(s) {planets[4]['rashi_lord']} 
        
            * Awastha (State): {planets[4]['awastha']} 
            * Karakamsha Role: {planets[4]['karakamsha']} 
            * **{planets[5]['name']} 

            * Sign: {planets[5]['sign']} 
            * House: {planets[5]['house']} 
            * Degree: {planets[5]['degree']} 
            * Nakshatra: {planets[5]['nakshatra']}, Pada: {planets[5]['nakshatra_pada']}, Nakshatra Lord: {planets[5]['nakshatra_lord']}
            * Retrograde: {planets[5]['retrograde']} 
            * Combust: {planets[5]['combust']} 
            * House Lordship: Lord of House(s) {planets[5]['rashi_lord']} 
            
            * Awastha (State): {planets[5]['awastha']} 
            * Karakamsha Role: {planets[5]['karakamsha']} 
            * **{planets[6]['name']} 

            * Sign: {planets[6]['sign']} 
            * House: {planets[6]['house']} 
            * Degree: {planets[6]['degree']} 
            * Nakshatra: {planets[6]['nakshatra']}, Pada: {planets[6]['nakshatra_pada']}, Nakshatra Lord: {planets[6]['nakshatra_lord']}
            * Retrograde: {planets[6]['retrograde']} 
            * Combust: {planets[6]['combust']} 
            * House Lordship: Lord of House(s) {planets[6]['rashi_lord']} 

            * Awastha (State): {planets[6]['awastha']} 
            * Karakamsha Role: {planets[6]['karakamsha']}
            * **{planets[7]['name']} 

            * Sign: {planets[7]['sign']} 
            * House: {planets[7]['house']} 
            * Degree: {planets[7]['degree']} 
            * Nakshatra: {planets[7]['nakshatra']}, Pada: {planets[7]['nakshatra_pada']}, Nakshatra Lord: {planets[7]['nakshatra_lord']}
            * Retrograde: {planets[7]['retrograde']} 
            * Combust: {planets[7]['combust']} 
            * House Lordship: Lord of House(s) {planets[7]['rashi_lord']} 
            
            * Awastha (State): {planets[7]['awastha']} 
            * Karakamsha Role: {planets[7]['karakamsha']} 
            * **{planets[8]['name']} 

            * Sign: {planets[8]['sign']} 
            * House: {planets[8]['house']} 
            * Degree: {planets[8]['degree']} 
            * Nakshatra: {planets[8]['nakshatra']}, Pada: {planets[8]['nakshatra_pada']}, Nakshatra Lord: {planets[8]['nakshatra_lord']}
            * Retrograde: {planets[8]['retrograde']} 
            * Combust: {planets[8]['combust']} 
            * House Lordship: Lord of House(s) {planets[8]['rashi_lord']} 
            
            * Awastha (State): {planets[8]['awastha']} 
            * Karakamsha Role: {planets[8]['karakamsha']} 
        * **Planetary Periods (Vimshottari Dasha System):


        * Current Maha Dasha (MD): {current_maha_dasha}(Running from {dates[0]} to {dates[1]})
        * Current Antar Dasha (AD): {current_antar_dasha}(Running from {dates[2]} to {dates[3]})
        * Current Pratyantar Dasha (PD): {current_pratyantar_dasha} (Running from {dates[4]} to {dates[5]})

        * Sadhe Sati Status: {sade_sathi_result}
        * **Key Yogas & Doshas Present:**
        * Major Positive Yogas Found: {present_yogas} 
        * Major Challenging Yogas/Doshas Found: {present_yogas} 
        * Kaal Sarpa Yoga Status: {kaal_sarpa_yoga_result} 
        * Manglik Dosha Status: {manglik_present} 



    ## 4. Instructions for AI Response Generation

    * **Role & Tone:** Act as a wise, compassionate, and objective Vedic Astrologer. Your tone should be supportive, clear, respectful, and non-fatalistic. Avoid sensationalism or fear-mongering.
    * **Basis of Interpretation:** Base ALL astrological interpretations *strictly* on the provided Kundli details (Section 3). Do not invent astrological data or influences. If information is missing (e.g., a specific divisional chart), state that you cannot analyze that specific aspect accurately. Consider planetary strengths (Shadbala) and relationships (natural/temporary friendships based on placements) when relevant.
    * **Answering Queries:** Directly address the user's specific query. Use the relevant parts of the Kundli (planets, houses, signs, dashas, transits, yogas, doshas, strengths) to formulate your answer. Explain *why* a certain interpretation is being made (e.g., "Mars in the 10th house, as lord of the 1st and 6th, suggests...").
    * **Clarity & Structure:** Provide answers in a clear, structured manner. Use paragraphs or bullet points for readability. Explain complex astrological terms briefly if necessary.
    * **Scope:** Stick to Vedic Astrology principles (primarily Parashari). Do not mix astrological systems (e.g., Western, Chinese) unless explicitly part of the user query and you have the necessary data/capabilities.
    * **Holistic View:** Consider the chart holistically. Don't overemphasize a single placement or aspect in isolation. Balance positive and challenging indications found in yogas, doshas, and planetary placements/strengths.
    * **Focus:** Emphasize potential, tendencies, timing of events (based on Dasha/Transits), and areas for personal growth or caution.
    * **Remedies :** If configured to suggest remedies, focus on traditional, constructive, and ethical suggestions (e.g., mantras, fasting, charity, gemstone recommendations *with caveats*, behavioural adjustments). Clearly state these are traditional suggestions and their efficacy varies. Avoid potentially harmful or superstitious practices. Check app guidelines on remedy suggestions. *Do not simply repeat remedies listed in API outputs if any were provided here; generate suggestions based on your analysis and instructions.*
    * **Personalization:** Address the user by their name (`{user_name}`). Tailor the language and depth of explanation appropriately.
    * **Current Time Context:** Use the current date ({today_date}) when interpreting Dashas and Transits.
    * **Brevity:** Be brief in your responses. Your responses are sent over a messaging app such as Whatsapp, so ease of consumption is an important consideration.

    ## 5. Important Considerations & Limitations (Ethical Guardrails)

    * **No Fortune-Telling:** Do not present predictions as absolute certainties. Emphasize that astrology shows tendencies and potentials, but free will and effort play a crucial role. Use probabilistic language (e.g., "suggests," "indicates," "potential for," "tendency towards").
    * **No Harmful Content:** Do not provide interpretations that are overly negative, fatalistic, discriminatory, or could cause undue distress.
    * **Professional Advice:** Explicitly state that you are an AI astrological guide and cannot provide medical, legal, financial (beyond general astrological indications of wealth potential/risk), or psychological advice. Advise users to consult qualified professionals for such matters.
    * **Respect Boundaries:** Avoid making intrusive judgments about the user's life or choices. Stick to interpreting the astrological chart in relation to their query.
    * **Confidentiality:** Treat user data with confidentiality (as per system design).

    ---

    **Context of Interaction:** You will receive specific queries from `{user_name}`. Use the comprehensive Kundli context provided above to analyze the query and generate a helpful, accurate, and ethical response based on Vedic Astrology principles.
    This is the query:{query_text}.Limit response to 200 words

    '''

        llm_start = time.time()
        content,model_name,model_version,tokens,cost=call_litellm(system_prompt)
        llm_end = time.time()   
        log_point_to_db(health_metric="q_and_a_kundli_node", phase="llm_time", latency=llm_end-llm_start, model=model_name, model_version= model_version, tokens=tokens,cost=cost,success= True)
        store = store_detail.objects.create(
    message_text=content,
    user_id=chat_id,
    metric="q_and_a_kundli_node",message_id=message_id,message_type=message_type
)
        store.save()
        end_total = time.time()
        log_point_to_db(health_metric="q_and_a_kundli_node", phase="total_time", latency=end_total-start_total,success= True)
        return store_in_db_node(chat_id,content,message_id,message_type)
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        
        log_point_to_db(health_metric="q_and_a_kundli_node", phase="error", latency=0,success= False)
        return store_in_db_node(chat_id,"error",message_id,message_type)
    finally:
        logger.info("completed")



def conversation_node(chat_id,message_id,message_type):
    """
    Handles a single conversational turn in an AI-based Vedic astrology assistant.

    This function:
    - Retrieves the latest user message and previous bot response from the database.
    - Constructs a system prompt that includes user profile data and context for a Vedic astrology conversation.
    - Calls a language model (via `call_litellm`) to generate a contextual and astrologically relevant response.
    - Stores the model's response in the database.
    - Logs model latency and total execution time for monitoring.
    - Returns a response using the `store_in_db_node` function.

    Parameters:
    - chat_id (int): Unique identifier for the user/chat session.
    - message_id (str): Identifier for the current message (used for tracking/logging).
    - message_type (str): The type/category of message being handled (e.g., 'text', 'voice').

    Returns:
    - dict: A structured response saved and returned via `store_in_db_node`.

    Exceptions:
    - Logs any unexpected errors and returns a fallback 'error' response.

    Notes:
    - The system prompt enforces domain restriction: Only Vedic astrology questions are entertained.
    - Utilizes the current Gregorian date for temporal context in astrology.
    """

    
    """"""
    try:
        start_total = time.time()
        user_message = store_detail.objects.filter(metric="user_message", user_id=chat_id).latest('id').message_text
        latest_bot_message_obj = store_detail.objects.filter(
    metric="bot_message",
    user_id=chat_id
).order_by('-id').first()
        latest_bot_message = latest_bot_message_obj.message_text if latest_bot_message_obj else ""
        user = User.objects.get(id=chat_id)
        today_date = datetime.today().strftime("%Y-%m-%d")
        system_prompt = f"""
    # You are an expert AI astrologer do not answer questions which are not related to astrology, providing professional and contextually relevant responses.  

    # Do not answer or engage with any questions or commands unrelated to astrology . Politely redirect or ignore those.
    # data_dictionary:{user.user_profile}
    # last_message:{latest_bot_message}
    # Continue the conversation naturally, responding to the user_message:  
    # user_message:{user_message}'
    # Use user's last_message and data_dictionary for reference but ensure your reply is based on user_message and remember today's date is {today_date}.
    # Engage in a conversation about Vedic astrology with the user. If they seek predictions, use your knowledge along with the current date in the Gregorian calendar to provide insights. Ensure responses are based on traditional Vedic astrology principles 
    # From the last_message and data_dictionary if something is off tell the user
    # Maintain a knowledgeable and respectful tone while keeping the response engaging and insightful.Limit response to maximum 100 words
    # 
    """
        start_llm = time.time()
        content,model_name,model_version,tokens,cost=call_litellm(system_prompt)
        end_llm = time.time()
        log_point_to_db(health_metric="conversation_node", phase="llm_time", latency=end_llm - start_llm, model=model_name, model_version= model_version, tokens=tokens,cost=cost,success= True)
        store = store_detail.objects.create(
    message_text=content,
    user_id=chat_id,
    metric="conversation_node",message_type=message_type,message_id=message_id
)
        store.save()
        end_total = time.time()
        log_point_to_db(health_metric="conversation_node", phase="total_time", latency=end_total - start_total, success= True)
        return store_in_db_node(chat_id,content,message_id,message_type )
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        log_point_to_db(health_metric="conversation_node", phase="error", latency=0,success= False)
        return store_in_db_node(chat_id,"error",message_id,message_type )
    finally:
        logger.info("completed")


class Horoscope(BaseModel):
    name:str
    time:str
    dob:str

class Kundli(BaseModel):
    full_name: str
    gender: str
    lat: str
    lon: str
    tzone: str
    day: str
    month: str
    year: str
    hour: str
    min: str
    sec: str
    place:str
  

def after_kundli_node(chat_id,message_id,message_type):
    """
    Handles the final step after a Kundli (birth chart) PDF is successfully generated.

    This function:
    - Updates the user's state to indicate the Kundli flow has ended.
    - Logs a success message indicating the Kundli PDF generation is complete.
    - Saves the message in the database with appropriate metadata.
    - Logs the total processing time for performance tracking.
    - Returns a confirmation response via `store_in_db_node`.

    Parameters:
    - chat_id (int): Unique identifier of the user.
    - message_id (str): ID associated with the current message event.
    - message_type (str): The type of message, e.g., 'text', 'status'.

    Returns:
    - dict: A structured message saved and returned via `store_in_db_node`.

    Exceptions:
    - Catches and logs any unexpected errors, returning a generic "error" response.

    Notes:
    - This function should be called only after a Kundli has been generated and saved.
    - Updates the `kundli_flow` flag in the user model to `False`.
    """

    try:
        start_total = time.time()
        content='Kundli PDF generated successfully'
        user=User.objects.get(id=chat_id)
        user.kundli_flow=False
        user.save()
        store = store_detail.objects.create(
    message_text=content,
    user_id=chat_id,
    metric="after_kundli_node",message_id=message_id,message_type=message_type
)
        store.save()
        end_total = time.time()
        log_point_to_db(health_metric="after_kundli_node", phase="total_time", latency=end_total - start_total, success= True)
        return store_in_db_node(chat_id,content,message_id,message_type)
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        log_point_to_db(health_metric="after_kundli_node", phase="error", latency=0,success= False)
        return store_in_db_node(chat_id,"error",message_id,message_type)
    finally:
        logger.info("completed")


def format_horoscope(prediction_data):
    """
    Formats the horoscope prediction data into a user-friendly string message.

    This function:
    - Extracts name, zodiac sign, and predictions from the input dictionary.
    - Formats the output in a readable format with emojis, titles, and line breaks.
    - Handles both string and list types within the predictions.

    Parameters:
    - prediction_data (dict): A dictionary containing horoscope details with the following keys:
        - 'name' (str): The name of the person.
        - 'zodiac_sign' (str): The zodiac sign of the person.
        - 'predictions' (dict): A dictionary where keys are prediction categories and values are strings or lists of strings.

    Returns:
    - str: A formatted string representing the horoscope.

    Exceptions:
    - Logs any exception that occurs during formatting and silently fails (returns `None`)."""
    try:
        name = prediction_data['name']
        zodiac = prediction_data['zodiac_sign']
        predictions = prediction_data['predictions']
        
        formatted_output = f"🌟 Horoscope for {name} ({zodiac}) 🌟\n\n"
        
        for key, value in predictions.items():
            # Capitalize the key and replace underscores with spaces
            formatted_key = key.capitalize().replace("_", " ")
            if isinstance(value, list):
                # Join list items with line breaks
                formatted_value = "\n- " + "\n- ".join(value)
            else:
                formatted_value = value
            formatted_output += f"{formatted_key}:\n{formatted_value}\n\n"

        return formatted_output
    except Exception as e:
        logger.error(f"Error {e}")

def format_weekly_horoscope(prediction_data):
    """
    Formats weekly horoscope prediction data into a human-readable string.

    This function:
    - Extracts name, zodiac sign, week, and predictions from the input dictionary.
    - Constructs a nicely formatted horoscope message.
    - Supports both string and list values for prediction categories.
    - Adds appropriate emojis and formatting for a better user experience.

    Parameters:
    - prediction_data (dict): A dictionary with the following keys:
        - 'name' (str): The person's name.
        - 'zodiac_sign' (str): The zodiac sign of the person.
        - 'week' (str, optional): The week or date range the horoscope applies to.
        - 'predictions' (dict): A dictionary of prediction categories. Each value can be a string or a list of strings.

    Returns:
    - str: A formatted string containing the weekly horoscope.

"""
    try:
        name = prediction_data['name']
        zodiac = prediction_data['zodiac_sign']
        week = prediction_data.get('week', None)
        predictions = prediction_data['predictions']

        # Header
        formatted_output = f"🌟 Horoscope for {name} ({zodiac}) 🌟\n"
        if week:
            formatted_output += f"📅 Week: {week}\n"
        formatted_output += "\n"

        # Predictions
        for key, value in predictions.items():
            formatted_key = key.capitalize().replace("_", " ")
            if isinstance(value, list):
                formatted_value = "\n- " + "\n- ".join(value)
            else:
                formatted_value = value
            formatted_output += f"{formatted_key}:\n{formatted_value}\n\n"

        return formatted_output
    except Exception as e:
        logger.error(f"Error {e}")





def after_horoscope_node(chat_id,message_id,message_type,set,data):
  
    """
    Handles post-horoscope processing after horoscope predictions have been generated.

    Depending on the type of horoscope (daily or weekly), this function:
    - Formats the prediction content using the appropriate formatter.
    - Updates the user's flow flags (e.g., daily_horoscope_flow or weekly_horoscope_flow) to False.
    - Saves the formatted message in the store_detail database.
    - Logs the total time taken for processing.
    - Returns the stored message using the `store_in_db_node` function.

    Parameters:
    - chat_id (int): Unique identifier for the user/chat.
    - message_id (str): Unique identifier for the message.
    - message_type (str): Type of the message, used for tracking or categorization.
    - set (str): A string indicating the type of horoscope, e.g., 'daily horoscope' or 'weekly horoscope'.
    - data (dict): The data payload containing horoscope prediction info under `data['data']`.

    Returns:
    - str: The result of the `store_in_db_node` function containing the formatted horoscope message.
"""
    try:
        start_total = time.time()

        system_prompt=''
        content=''
        # data=json.loads(content)
        user=User.objects.get(id=chat_id)
        
        if 'daily horoscope' in set:
            content=format_horoscope(data['data'])
            user.daily_horoscope_flow=False
        if 'weekly horoscope' in set:
            content=format_weekly_horoscope(data['data'])
            user.weekly_horoscope_flow=False

        user.save()
        store = store_detail.objects.create(
    message_text=content,
    user_id=chat_id,
    metric="after_horoscope_node",message_id=message_id,message_type=message_type
)
        store.save()
        end_total = time.time()
        print(content)
        log_point_to_db(health_metric="after_horoscope", phase="total_time", latency= end_total - start_total, success= True)
        return store_in_db_node(chat_id,content,message_id,message_type)
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        log_point_to_db(health_metric="after_horoscope_node", phase="error", latency=0,success= False)
        return store_in_db_node(chat_id,"error",message_id,message_type)
    finally:
        logger.info("completed")



def horoscope_node(chat_id,decision,message_id,message_type):
    """
    Handles the generation of a daily horoscope for a user based on available or inferred personal details.

    This function:
    - Retrieves the latest user and bot messages from the database.
    - Constructs a system prompt to extract missing horoscope-related details (e.g., name, date of birth, time).
    - Uses a language model (with fallback options) to infer or extract these details.
    - If all essential information is present, it calls `call_horoscope()` to generate the daily horoscope.
    - If information is incomplete, it formulates a new prompt to request missing details and stores the model's reply.
    - Tracks latency, token usage, model version, and cost at different phases for observability.
    - Stores both user-facing and internal outputs in the database.

    Parameters:
    - chat_id (int): The unique identifier for the user or chat session.
    - decision (str): Additional input or context used in horoscope generation logic.
    - message_id (int): Identifier of the current message being processed.
    - message_type (str): Type of message (e.g., "text", "voice").

    Returns:
    - If all required details are available: The result of `call_horoscope()`, which generates the final horoscope.
    - If details are missing: A message asking for more information is stored and returned via `store_in_db_node()`.
    - On failure: Logs the error and stores a fallback error message.
    """

    try:
        start_total = time.time()
        details = {}
        user = User.objects.get(id=chat_id)
        latest_message = store_detail.objects.filter(metric="user_message", user_id=chat_id).latest('id').message_text
        latest_bot_message_obj = store_detail.objects.filter(
    metric="bot_message",
    user_id=chat_id
).order_by('-id').first()

        latest_bot_message = latest_bot_message_obj.message_text if latest_bot_message_obj else ""
        today_date = datetime.today().strftime("%Y-%m-%d")
        system_prompt=HOROSCOPE_MISSING_DETAILS_PROMPT.format(last_message=latest_message,last_10_contents=latest_bot_message,user_profile=user.user_profile,today_date=today_date,Horoscope=Horoscope)
        start_llm = time.time()
        model_write=''
        for model in model_fallback_list:
            model_write=model
            try:
                response = completion(
            model=model,
            response_format=Horoscope,
            messages=[{ "content": system_prompt,"role": "user"}]
            )
                break
            except Exception as e:
                logger.error(f"error occurred: {e}")
        end_llm = time.time()
        model_name=model_write.split('/')[0]
        model_version=model_write.split('/')[1]
        cost = completion_cost(completion_response=response)
        tokens=token_counter( model=model_write,
    messages=[{ "content": system_prompt,"role": "user"}])
        log_point_to_db(health_metric="horoscope_node", phase="llm_fetch_missing_details_time", latency=end_llm - start_llm, model=model_name, model_version= model_version, tokens=tokens,cost=cost,success= True)
        content=response.choices[0].message.content
        details=json.loads(content)

        if (
            len(details.get("name")) > 0
            and len(details.get("dob")) > 0
            and len(details.get("time")) > 0
        ):
            end_total = time.time()
            log_point_to_db(health_metric="horoscope_node", phase="total_time", latency= end_total - start_total,  success= True)
            return call_horoscope(details,chat_id,decision,message_id,message_type)
        details=str(details)
        system_prompt=HOROSCOPE_ASK_DETAILS_PROMPT.format(last_message=latest_message,details=details)
        llm_start_missing_details = time.time()
        response=''

        content,model_name,model_version,tokens,cost=call_litellm(system_prompt)
        llm_end_missing_details = time.time()

        log_point_to_db(health_metric="horoscope_node", phase="llm_ask_missing_details_time", latency= llm_end_missing_details - llm_start_missing_details, model=model_name, tokens=tokens,cost=cost,model_version= model_version, success= True)

        store = store_detail.objects.create(
    message_text=content,
    user_id=chat_id,
    metric="horoscope_node",message_id=message_id,message_type=message_type
)
        store.save()
        end_total=time.time()
        log_point_to_db(health_metric="horoscope_node", phase="total_time", latency= end_total - start_total,  success= True)
        return store_in_db_node(chat_id,content,message_id,message_type)

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        log_point_to_db(health_metric="horoscope_node", phase="error", latency=0,success= False)
        return store_in_db_node(chat_id,"error",message_id,message_type)
    finally:
        logger.info("completed")


















def build_state_graph(user_message, chat_id, message_id, user_message_type):
    """
    Builds or updates a Langgraph based on the user's message and chat ID.


    Parameters:
    - user_message (str): The message input from the user that will influence the graph logic.
    - chat_id (str or int): The unique identifier for the chat session or user.

    Returns:
    - dict or None: A dictionary representing the state graph if built successfully, else None.

    Notes:
    - The function is expected to parse the message and update a stateful context or graph.
    - Exceptions are handled internally, with errors printed to the console.
    """
    try:

        profile, created = User.objects.get_or_create(
            id=chat_id, defaults={"user_profile": {}}
        )
        store = store_detail.objects.create(
        message_text=user_message,
        user=profile,
        metric="user_message",
        message_id=message_id,message_type=user_message_type
    )
        store.save()

        response_text=intent_node(user_message,chat_id,message_id,user_message_type)
    

        today_date = datetime.today().strftime("%Y-%m-%d")
        if "Kundli PDF generated successfully" in response_text:

            # telegram_interface.utils.send_telegram_document(chat_id, f"{chat_id}_kundli.pdf")

            os.remove(f"{chat_id}_kundli.pdf")
            for i in range(1,20):
                if os.path.exists(f"page{i}_mp_{chat_id}.pdf"):
                    os.remove(f"page{i}_mp_{chat_id}.pdf")
                    os.remove(f"page{i}_output_{chat_id}.html")
                    logger.info(f"Removed:")
                else:
                    logger.info(f"File not found:" )
       
            return f"https://astro-ai.s3.ap-south-1.amazonaws.com/{chat_id}_kundli.pdf"
        return response_text
    except Exception as e:
        logger.error(f"Error {e}")
        return "Type again"

def build_state_graph_test(user_message, chat_id, message_id, user_message_type):
    """
    Builds or updates a Langgraph based on the user's message and chat ID.


    Parameters:
    - user_message (str): The message input from the user that will influence the graph logic.
    - chat_id (str or int): The unique identifier for the chat session or user.

    Returns:
    - dict or None: A dictionary representing the state graph if built successfully, else None.

    Notes:
    - The function is expected to parse the message and update a stateful context or graph.
    - Exceptions are handled internally, with errors printed to the console.
    """
    try:

        profile, created = User.objects.get_or_create(
            id=chat_id, defaults={"user_profile": {}}
        )
        store = store_detail.objects.create(
        message_text=user_message,
        user=profile,
        metric="user_message",
        message_id=message_id,message_type=user_message_type
    )
        store.save()

        response_text=intent_node(user_message,chat_id,message_id,user_message_type)
    

        # today_date = datetime.today().strftime("%Y-%m-%d")
        if "Kundli PDF generated successfully" in response_text:

            # telegram_interface.utils.send_telegram_document(chat_id, f"{chat_id}_kundli.pdf")

            os.remove(f"{chat_id}_kundli.pdf")
            for i in range(1,20):
                if os.path.exists(f"page{i}_mp_{chat_id}.pdf"):
                    os.remove(f"page{i}_mp_{chat_id}.pdf")
                    os.remove(f"page{i}_output_{chat_id}.html")
                    logger.info(f"Removed:")
                else:
                    logger.info(f"File not found:" )
       
            return ""
        return response_text
    except Exception as e:
        logger.error(f"Error {e}")
        return "Type again"


        

def test(user_message,user_id):
    response_text = build_state_graph(user_message, user_id, 100, LogType.USER.value)
    return response_text

def build_state_graph_notification(user_message, chat_id, message_id, user_message_type,graph):

    """
    Builds or updates a Langgraph based on the user's message and chat ID.


    Parameters:
    - user_message (str): The message input from the user that will influence the graph logic.
    - chat_id (str or int): The unique identifier for the chat session or user.

    Returns:
    - dict or None: A dictionary representing the state graph if built successfully, else None.

    Notes:
    - The function is expected to parse the message and update a stateful context or graph.
    - Exceptions are handled internally, with errors printed to the console.
    """
 

    compile_start = time.time()
  

    
    compile_end = time.time()

    config = {"configurable": {"thread_id": str(chat_id)}}

    user_input = user_message
    user_fetch_start = time.time()
    profile, created = User.objects.get_or_create(
        id=chat_id, defaults={"user_profile": {}}
    )
    user_fetch_end = time.time()
    if settings.LOAD_TEST_MODE:
        log_time_to_csv(chat_id, user_message_type, message_id, "user_db_get_create_time", user_fetch_end - user_fetch_start)
  
    
    graph_run_start = time.time()

    # The config is the **second positional argument** to stream() or invoke()!
    events = graph.stream(
        {
            "user_message": [{"role": "user", "content": user_input}],
            "thread_id": str(chat_id),
            "message_id": str(message_id),
            "user_message_type": str(user_message_type),
       
        },
        config,
        stream_mode="values",
    )
    for event in events:
        if event["messages"]:
            response_text = event["messages"][-1].content
    graph_run_end = time.time()
    if settings.LOAD_TEST_MODE:
        log_time_to_csv(chat_id, user_message_type, message_id, "langraph_execution_time", graph_run_end - graph_run_start)
    today_date = datetime.today().strftime("%Y-%m-%d")
    if "Kundli PDF generated successfully" in response_text:
        pdf_send_start = time.time()
        telegram_interface.utils.send_telegram_document(chat_id, f"{chat_id}_kundli.pdf")
        os.remove(f"{chat_id}_kundli.pdf")
        for i in range(1,20):
            if os.path.exists(f"page{i}_mp_{chat_id}.pdf"):
                os.remove(f"page{i}_mp_{chat_id}.pdf")
                os.remove(f"page{i}_output_{chat_id}.html")
                logger.info(f"Removed:")
            else:
                logger.info(f"File not found: ")
        return ""
        pdf_send_end = time.time()
        # if settings.LOAD_TEST_MODE:
        #     log_time_to_csv(chat_id, user_message_type, message_id, "kundli_pdf_send_time", pdf_send_end - pdf_send_start)
        return ""
    elif "Horoscope PDF generated successfully" in response_text:
        telegram_interface.utils.send_telegram_document(chat_id, f"{chat_id}_horoscope_{today_date}.pdf")
        return ""

    return response_text

# def test(user_message):
#     response_text = build_state_graph(user_message, 100, 100, LogType.USER.value)
#     return response_text


def run_llm_pipeline(user_message, memory, platform, chat_id, message_id, user_message_type):

    """
    Executes the LLM pipeline with a continuous typing indicator in the background.

    This function performs the following:
    - Starts a typing action on the specified chat platform using a background thread.
    - Processes the user's message using the `build_state_graph` function.
    - Measures and logs the core LangGraph processing time if load testing is enabled.
    - Stops the typing action once processing is complete or if an exception occurs.

    Parameters:
    - user_message (str): The message sent by the user.
    - memory (any): Memory or context for the chat (currently unused in this function).
    - platform (str): The chat platform (e.g., WhatsApp, Telegram) (currently unused).
    - chat_id (int): Unique identifier for the user/chat session.
    - message_id (str): Unique identifier for the message.
    - user_message_type (str): The type or category of the user message (e.g., 'text', 'image').

    Returns:
    - str: The response generated by the `build_state_graph` pipeline.

    Exceptions:
    - Any exception during processing is logged, and the typing indicator is properly shut down.

    Notes:
    - The typing indicator runs in a background thread and is canceled safely after processing.
    - The function assumes `send_typing_action` and `build_state_graph` are defined elsewhere.
    - Logging to CSV is conditional on the `LOAD_TEST_MODE` flag in settings.
    """
    try:
        stop_typing_event = threading.Event()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Start typing indicator in background
            typing_future = executor.submit(telegram_interface.utils.send_typing_action, chat_id, stop_typing_event)
            
            try:
                # Run the main graph processing
                core_langraph_start = time.time()
                response_text = build_state_graph(user_message, chat_id, message_id, user_message_type)
                core_langraph_end = time.time()
                if settings.LOAD_TEST_MODE:
                    log_time_to_csv(chat_id, user_message_type, message_id, "core_langraph_pipeline_time", core_langraph_end - core_langraph_start)
                return response_text
            finally:
                # Ensure typing indicator is stopped
                stop_typing_event.set()
                typing_future.cancel()
    except Exception as e:
        logger.error(f"Error {e}")

def run_llm_pipeline_notification(user_message, memory, platform, chat_id, message_id, user_message_type,graph):
    """Runs the LLM pipeline with continuous typing indicator"""
    stop_typing_event = threading.Event()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Start typing indicator in background
        typing_future = executor.submit(telegram_interface.utils.send_typing_action, chat_id, stop_typing_event)
        
        try:
            # Run the main graph processing
            core_langraph_start = time.time()
            response_text = build_state_graph_notification(user_message, chat_id, message_id, user_message_type,graph)
            core_langraph_end = time.time()
            if settings.LOAD_TEST_MODE:
                log_time_to_csv(chat_id, user_message_type, message_id, "core_langraph_pipeline_time", core_langraph_end - core_langraph_start)
            return response_text
        finally:
            # Ensure typing indicator is stopped
            stop_typing_event.set()
            typing_future.cancel()


def postprocess_response(response_text):
    response_text = response_text.strip()
    response_text = re.sub(r"\s+", " ", response_text)
    words = response_text.split()
    if len(words) > 60:
        response_text = " ".join(words[:60]) + "..."
    return response_text


# def generate_transcription_from_audio(path):
#     """Transcribes audio to text using OpenAI Whisper."""
#     try:
#         client = OpenAI(api_key=openai_api_key)
#         with open(path, "rb") as audio_file:
#             transcription = client.audio.transcriptions.create(
#                 model="whisper-1", file=audio_file
#             )
#         return transcription.text
#     except Exception as e:
#         logger.error(f"Failed to transcribe audio: {e}")
#         return None



# with open("config.json", "r") as f:
#     config = json.load(f)


# def text_to_speech(text, output_file="response.mp4"):
#     """Converts text to speech using multiple providers and saves as MP4."""
#     try:
#         provider = config.get("tts_provider", "amazon_polly")
#         mp3_file = "response.mp3"

#         if provider == "amazon_polly":
#             polly_client = boto3.client(
#                 "polly",
#                 aws_access_key_id=config["aws_access_key"],
#                 aws_secret_access_key=config["aws_secret_key"],
#                 region_name=config["region"],
#             )
#             response = polly_client.synthesize_speech(
#                 Text=text,
#                 OutputFormat="mp3",
#                 VoiceId=config["models"]["amazon_polly"]["voice"],
#             )
#             with open(mp3_file, "wb") as out:
#                 out.write(response["AudioStream"].read())

#         elif provider == "gtts":
#             # Google TTS
#             gtts_config = config["models"]["gtts"]
#             tts = gTTS(
#                 text=text, lang=gtts_config["language"], slow=gtts_config["slow"]
#             )
#             tts.save(mp3_file)

#         elif provider == "openai":
#             # OpenAI TTS API
#             openai_config = config["models"]["openai"]
#             headers = {"Authorization": f"Bearer {openai_config['api_key']}"}
#             data = {"input": text, "model": "tts-1", "voice": openai_config["voice"]}
#             response = requests.post(
#                 "https://api.openai.com/v1/audio/speech", headers=headers, json=data
#             )
#             with open(mp3_file, "wb") as out:
#                 out.write(response.content)

#         elif provider == "elevenlabs":
#             # ElevenLabs API
#             elevenlabs_config = config["models"]["elevenlabs"]
#             headers = {
#                 "Content-Type": "application/json",
#                 "xi-api-key": elevenlabs_config["api_key"],
#             }
#             data = {
#                 "text": text,
#                 "voice_id": elevenlabs_config["voice_id"],
#                 "model_id": "eleven_multilingual_v1",
#             }
#             response = requests.post(
#                 "https://api.elevenlabs.io/v1/text-to-speech",
#                 headers=headers,
#                 json=data,
#             )
#             with open(mp3_file, "wb") as out:
#                 out.write(response.content)

#         else:
#             raise ValueError("Unsupported TTS provider")

#         # Convert MP3 to MP4 with speed adjustment
#         speed = config.get("speed", 1.0)  # Default speed is 1.0 (normal)
#         command = f"ffmpeg -y -i {mp3_file} -filter:a 'atempo={speed}' -c:a aac -b:a 192k -movflags +faststart {output_file}"
#         subprocess.run(command, shell=True, check=True)

#         logger.info(f"MP4 audio file saved: {output_file}")
#         return output_file

#     except Exception as e:
#         logger.error(f"Failed to convert text to speech: {e}")
#         return None

