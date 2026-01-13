import os
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.conf import settings
import json
import logging
from .utils import send_text_message, process_telegram_message, download_telegram_voice, process_telegram_message_audio_transcript, send_text_message_with_buttons
from langchain_agent.utils import  get_user_memory, run_llm_pipeline
from ai_services.utils.stt_utils import generate_stt, generate_with_deepgram_en
import asyncio
# from ai_services.utils.stt_utils import generate_stt
from langchain_agent.models import User,Logger
from langchain_agent.models import LogType
import time
from asgiref.sync import sync_to_async
from timing_test_csv_utils import log_time_to_csv
import influxdb_client_3
from influxdb_client_3 import InfluxDBClient3, Point, WriteOptions, WritePrecision
from dotenv import load_dotenv
from datetime import datetime
from context import set_request_context
from influx import log_point_to_db

# Create your views here.

logger = logging.getLogger(__name__)

load_dotenv()


INFLUX_HOST = os.getenv("INFLUX_HOST")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")


client = InfluxDBClient3(host=INFLUX_HOST, database=INFLUX_BUCKET, token=INFLUX_TOKEN)
# write_api = client.write_api()


def handle_telegram_message(request):
    """Handles incoming messages and updates from Telegram."""
    request_start_time = time.time()
    channel ="telegram"
    try:
        body = json.loads(request.body)
        logger.info(f"Incoming Telegram payload: {body}")
        print(body)
        msg_id=1

        
        if "message" in body:
            message = body["message"]
            chat_id = message["chat"]["id"]
            msg_id = message['message_id']

            if Logger.objects.filter(message_id=msg_id).exists():
                return JsonResponse({"status": "ok"}, status=200)  # Return response immediately if message_id exists

            if "voice" in message and message.get("voice"):
                message_type = "voice"
                Logger.objects.create(user_id=str(chat_id), message="voice message", log_type=LogType.USER.value,message_id=message['message_id'])
            else:
                message_type = "text"
                Logger.objects.create(user_id=str(chat_id), message=message['text'], log_type=LogType.USER.value,message_id=message['message_id'])

            set_request_context(str(msg_id), str(chat_id), channel, message_type)
            
            user_message = message.get("text", "")
            memory = get_user_memory(chat_id)

            

            processing_start_time = time.time()
            if settings.LOAD_TEST_MODE:
                log_time_to_csv(chat_id, message_type, msg_id, "initial", processing_start_time - request_start_time)  # ⏱️ Initial phase done

            if user_message.strip().replace(" ", "") == "/start":
                buttons = [
                    [
                        {"text": "Get Personalised Kundli", "callback_data": "get_kundli"},
                        {"text": "Share my Horoscope", "callback_data": "get_horoscope"}
                    ]
                ]
                send_text_message_with_buttons(chat_id, "Hi! I'm your personalised astrology bot", buttons)
                return JsonResponse({"status": "ok"}, status=200)


            if user_message:

                # point = (
                #                 Point("usage_metrics")
                #                 .tag("request_id", str(msg_id))
                #                 .tag("user_id", str(chat_id))
                #                 .tag("channel", "telegram")
                #                 .tag("request_type", "text")
                #             )
                logger.info(f"Received text message from {chat_id}: {user_message}")
                response_start = time.time()
                response_text = process_telegram_message(body, memory)  # Process message
                response_end = time.time()
                if response_text:
                    log_point_to_db(health_metric="text_response", phase="total_time", latency=response_end-request_start_time, success=True)
                else:
                    log_point_to_db(health_metric="text_response", phase="total_time", latency=response_end-request_start_time, success=False)
                if settings.LOAD_TEST_MODE:
                    log_time_to_csv(chat_id, message_type, msg_id, "processing", response_end - response_start)  # ⏱️ LLM/text processing

            elif "voice" in message:
                
                response_start = time.time()
                send_text_message(chat_id, "Analysing your audio request, please wait...")
                file_id = message["voice"]["file_id"]
                logger.info(f"Received voice message from {chat_id}. File ID: {file_id}")
                download_voice_start = time.time()
                file_path = download_telegram_voice(file_id, chat_id)
                download_voice_end = time.time()
                
                if settings.LOAD_TEST_MODE:
                    log_time_to_csv(chat_id, message_type, msg_id, "download_voice", (download_voice_end-download_voice_start))
                if file_path:
                    stt_start = time.time()
                    transcription, lang_id, confidence = asyncio.run(generate_with_deepgram_en(file_path, "nova-3"))
                    if lang_id!= 'en':
                        transcription = generate_stt(file_path)
                    stt_end = time.time()
                    if settings.LOAD_TEST_MODE:
                        log_time_to_csv(chat_id, message_type, msg_id, "STT", (stt_end-stt_start))
                    # REMOVE the voice file
                    # try:
                    #     os.remove(file_path)
                    #     print(f"Deleted file: {file_path}")
                    # except Exception as e:
                    #     print(f"Failed to delete file {file_path}: {e}")
                    if transcription:
                        logger.info(f"Transcription: {transcription}")
                        response_text = process_telegram_message_audio_transcript({
                            "message": {
                                "chat": {"id": chat_id},
                                "text": transcription,
                                "message_id": msg_id
                            }
                        }, memory, file_id)
                        response_end = time.time()
                        if response_text:
                            log_point_to_db(health_metric="voice_response", phase="total_time", latency=response_end-request_start_time, success=True)
                        else:
                            log_point_to_db(health_metric="voice_response", phase="total_time", latency=response_end-request_start_time, success=False)
                        if settings.LOAD_TEST_MODE:
                            log_time_to_csv(chat_id, message_type, msg_id, "processing", response_end - response_start)  # ⏱️ Audio processing
                    else:
                        logger.error("Failed to transcribe audio.")
                        response_end = time.time()
                        log_point_to_db(health_metric="voice_response", phase="total_time", latency=response_end-request_start_time, success=False)
                else:
                    logger.error("Failed to download audio file.")
                    response_end = time.time()
                    log_point_to_db(health_metric="voice_response", phase="total_time", latency=response_end-request_start_time, success=False)
                    
            
        elif "callback_query" in body:
            callback_query = body["callback_query"]
            chat_id = callback_query["message"]["chat"]["id"]
            msg_id = callback_query["message"]["message_id"]
            callback_query_id=callback_query['id']
                        
            if Logger.objects.filter(callback_query_id=callback_query_id).exists():
                return JsonResponse({"status": "ok"}, status=200)
            Logger.objects.create(user_id=str(chat_id), message="action_button", log_type=LogType.USER.value,message_id=msg_id,callback_query_id=callback_query_id)
            memory = get_user_memory(chat_id)
            current_query = body['callback_query']['data']
            message_type = "action_button"

            set_request_context(str(msg_id), str(chat_id), channel, message_type)
      

            if current_query == "get_horoscope":
                # First generate and send the horoscope
              
                initial_end = time.time()
                if settings.LOAD_TEST_MODE:
                    log_time_to_csv(chat_id, message_type, msg_id, "initial", initial_end - request_start_time) 
                langraph_start = time.time()
                response = run_llm_pipeline(current_query, memory=memory, platform="telegram", chat_id=chat_id, message_id=msg_id, user_message_type='text')
                langraph_end = time.time()
                if response:
                    log_point_to_db(action_button_category=current_query, health_metric="langgraph_pipeline", phase="total_time", latency= langraph_end -langraph_start, success=True)
                else:
                    log_point_to_db(action_button_category=current_query, health_metric="langgraph_pipeline", phase="total_time", latency= langraph_end -langraph_start, success=False)
                if settings.LOAD_TEST_MODE and response:
                    log_time_to_csv(chat_id, "text", msg_id, "langraph_pipeline_time", langraph_end - langraph_start)
                send_text_message(chat_id, response)

                # Then send the notification preference buttons
                
                buttons = [
                    [
                        {"text": "Receive Daily Horoscope", "callback_data": "daily_horoscope"},
                        {"text": "Receive Weekly Horoscope", "callback_data": "weekly_horoscope"}
                    ],
                    [
                        {"text": "Please Don't Send Notifications", "callback_data": "no_notifications"}
                    ]
                ]
                
                send_text_message_with_buttons(
                    chat_id, 
                    "Would you like to receive regular horoscope updates?",
                    buttons
                )
                response_end = time.time()
                if response:
                    log_point_to_db(action_button_category=callback_query, health_metric= "action_button_response", phase="total_time", latency=response_end-request_start_time, success=True)
                else:
                    log_point_to_db(action_button_category=callback_query, health_metric= "action_button_response", phase="total_time", latency=response_end-request_start_time, success=False)
            
            elif current_query in ["daily_horoscope", "weekly_horoscope", "no_notifications"]:
                frequency_map = {
                    "daily_horoscope": "daily",
                    "weekly_horoscope": "weekly",
                    "no_notifications": "no"
                }

                try:
                    # Get the user and update their profile
                    user = User.objects.filter(id=str(chat_id)).first()
                    user_profile = user.user_profile if user.user_profile else {}
                    user_profile["notifications_frequency"] = frequency_map[current_query]
                    user.user_profile = user_profile
                    user.save()
                    print("Updated user profile:", user.user_profile)

                    # Send confirmation message
                    if current_query == "daily_horoscope":
                        response = "You'll receive daily horoscope updates. You can change this preference anytime."
                    elif current_query == "weekly_horoscope":
                        response = "You'll receive weekly horoscope updates. You can change this preference anytime."
                    else:
                        response = "You won't receive any horoscope notifications. You can change this preference anytime."
                    send_text_message(chat_id, response) 
                    response_end = time.time()
                    log_point_to_db(action_button_category="notification_preference", health_metric= "action_button_response", phase="total_time", latency=response_end-request_start_time, success=True)

                except User.DoesNotExist:
                    logger.error(f"User {chat_id} not found when trying to update notification preferences")
                    send_text_message(chat_id, "Sorry, there was an error updating your preferences. Please try again later.")
                    response_end = time.time()
                    log_point_to_db(action_button_category="notification_preference", health_metric= "action_button_response", phase="total_time", latency=response_end-request_start_time, success=False)
                except Exception as e:
                    logger.error(f"Error updating user preferences: {str(e)}")
                    send_text_message(chat_id, "Sorry, there was an error updating your preferences. Please try again later.")
                    response_end = time.time()
                    log_point_to_db(action_button_category="notification_preference", health_metric= "action_button_response", phase="total_time", latency=response_end-request_start_time, success=False)
            
            
            else:
              
                initial_end = time.time()
                if settings.LOAD_TEST_MODE:
                    log_time_to_csv(chat_id, message_type, msg_id, "initial", initial_end - request_start_time) 
                langraph_start = time.time()
                response = run_llm_pipeline(current_query, memory=memory, platform="telegram", chat_id=chat_id,message_id=msg_id,user_message_type='text')
                langraph_end = time.time()
                if response:
                    log_point_to_db(action_button_category=current_query, health_metric="langgraph_pipeline", phase="total_time", latency= langraph_end -langraph_start, success=True)
                else:
                    log_point_to_db(action_button_category=current_query, health_metric="langgraph_pipeline", phase="total_time", latency= langraph_end -langraph_start, success=False)
                if settings.LOAD_TEST_MODE and response:
                    log_time_to_csv(chat_id, "text", msg_id, "langraph_pipeline_time", langraph_end - langraph_start)
                print(response)
                send_text_message(chat_id, response)

                response_end = time.time()
                if response:
                    log_point_to_db(action_button_category=callback_query, health_metric= "action_button_response", phase="total_time", latency=response_end-request_start_time, success=True)
                else:
                    log_point_to_db(action_button_category=callback_query, health_metric= "action_button_response", phase="total_time", latency=response_end-request_start_time, success=False)
                
            response_end = time.time()
            if settings.LOAD_TEST_MODE:
                log_time_to_csv(chat_id, message_type, msg_id, "processing", response_end - request_start_time) 

        return JsonResponse({"status": "ok"}, status=200)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")

        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    finally:
        connection.close()

# async def handle_telegram_message(request):
#     """Handles incoming messages and updates from Telegram asynchronously."""
#     request_start_time = time.time()
#     try:
#         body = json.loads(request.body)
#         logger.info(f"Incoming Telegram payload: {body}")
#         print(body)
#         msg_id = 1

#         if "message" in body:
#             message = body["message"]
#             chat_id = message["chat"]["id"]
#             msg_id = message['message_id']

#             if await sync_to_async(Logger.objects.filter(message_id=msg_id).exists)():
#                 return JsonResponse({"status": "ok"}, status=200)

#             if "voice" in message and message.get("voice"):
#                 message_type = "voice"
#                 await sync_to_async(Logger.objects.create)(
#                     user_id=str(chat_id),
#                     message="voice message",
#                     log_type=LogType.USER.value,
#                     message_id=message['message_id']
#                 )
#             else:
#                 message_type = "text"
#                 await sync_to_async(Logger.objects.create)(
#                     user_id=str(chat_id),
#                     message=message['text'],
#                     log_type=LogType.USER.value,
#                     message_id=message['message_id']
#                 )

#             user_message = message.get("text", "")
#             memory = await sync_to_async(get_user_memory)(chat_id)

#             processing_start_time = time.time()
#             if settings.LOAD_TEST_MODE:
#                 await sync_to_async(log_time_to_csv)(
#                     chat_id, message_type, msg_id, "initial", 
#                     processing_start_time - request_start_time
#                 )

#             if user_message.strip().replace(" ", "") == "/start":
#                 buttons = [
#                     [
#                         {"text": "Get Personalised Kundli", "callback_data": "get_kundli"},
#                         {"text": "Share my Horoscope", "callback_data": "get_horoscope"}
#                     ]
#                 ]
#                 await sync_to_async(send_text_message_with_buttons)(
#                     chat_id, "Hi! I'm your personalised astrology bot", buttons
#                 )
#                 return JsonResponse({"status": "ok"}, status=200)

#             if user_message:
#                 logger.info(f"Received text message from {chat_id}: {user_message}")
#                 response_start = time.time()
#                 response_text = await sync_to_async(process_telegram_message)(
#     body, 
#     memory)  # Assuming this is made async
#                 response_end = time.time()
#                 if settings.LOAD_TEST_MODE:
#                     await sync_to_async(log_time_to_csv)(
#                         chat_id, message_type, msg_id, "processing", 
#                         response_end - response_start
#                     )

#             elif "voice" in message:
#                 response_start = time.time()
#                 await sync_to_async(send_text_message)(
#                     chat_id, "Analysing your audio request, please wait..."
#                 )
#                 file_id = message["voice"]["file_id"]
#                 logger.info(f"Received voice message from {chat_id}. File ID: {file_id}")
#                 download_voice_start = time.time()
#                 file_path = await download_telegram_voice(file_id)  # Assuming this is made async
#                 download_voice_end = time.time()
                
#                 if settings.LOAD_TEST_MODE:
#                     await sync_to_async(log_time_to_csv)(
#                         chat_id, message_type, msg_id, "download_voice",
#                         (download_voice_end - download_voice_start)
#                     )
#                 if file_path:
#                     stt_start = time.time()
#                     transcription, lang_id, confidence = await generate_with_deepgram_en(file_path, "nova-3")
#                     if lang_id != 'en':
#                         transcription = await generate_stt(file_path)  # Assuming this is made async
#                     stt_end = time.time()
#                     if settings.LOAD_TEST_MODE:
#                         await sync_to_async(log_time_to_csv)(
#                             chat_id, message_type, msg_id, "STT", 
#                             (stt_end - stt_start)
#                         )
#                     if transcription:
#                         logger.info(f"Transcription: {transcription}")
#                         response_text = await process_telegram_message_audio_transcript({
#                             "message": {
#                                 "chat": {"id": chat_id},
#                                 "text": transcription,
#                                 "message_id": msg_id
#                             }
#                         }, memory)
#                         response_end = time.time()
#                         if settings.LOAD_TEST_MODE:
#                             await sync_to_async(log_time_to_csv)(
#                                 chat_id, message_type, msg_id, "processing",
#                                 response_end - response_start
#                             )
#                     else:
#                         logger.error("Failed to transcribe audio.")
#                 else:
#                     logger.error("Failed to download audio file.")
            
#         elif "callback_query" in body:
#             callback_query = body["callback_query"]
#             chat_id = callback_query["message"]["chat"]["id"]
#             memory = await sync_to_async(get_user_memory)(chat_id)
#             current_query = body['callback_query']['data']

#             if current_query == "get_horoscope":
#                 await sync_to_async(send_text_message)(
#                     chat_id, "Generating your horoscope..."
#                 )
#                 initial_end = time.time()
#                 if settings.LOAD_TEST_MODE:
#                     await sync_to_async(log_time_to_csv)(
#                         chat_id, message_type, msg_id, "initial",
#                         initial_end - request_start_time
#                     )
#                 langraph_start = time.time()
#                 response = await run_llm_pipeline(  # Assuming this is made async
#                     current_query, memory=memory, platform="telegram", 
#                     chat_id=chat_id, message_id=msg_id, user_message_type='text'
#                 )
#                 langraph_end = time.time()
#                 if settings.LOAD_TEST_MODE and response:
#                     await sync_to_async(log_time_to_csv)(
#                         chat_id, "text", msg_id, "langraph_pipeline_time",
#                         langraph_end - langraph_start
#                     )
#                 await sync_to_async(send_text_message)(chat_id, response)

#                 buttons = [
#                     [
#                         {"text": "Receive Daily Horoscope", "callback_data": "daily_horoscope"},
#                         {"text": "Receive Weekly Horoscope", "callback_data": "weekly_horoscope"}
#                     ],
#                     [
#                         {"text": "Please Don't Send Notifications", "callback_data": "no_notifications"}
#                     ]
#                 ]

#                 await sync_to_async(send_text_message_with_buttons)(
#                     chat_id,
#                     "Would you like to receive regular horoscope updates?",
#                     buttons
#                 )

#             elif current_query in ["daily_horoscope", "weekly_horoscope", "no_notifications"]:
#                 frequency_map = {
#                     "daily_horoscope": "daily",
#                     "weekly_horoscope": "weekly",
#                     "no_notifications": "no"
#                 }

#                 try:
#                     user = await sync_to_async(User.objects.filter(id=str(chat_id))).first()
#                     user_profile = user.user_profile if user.user_profile else {}
#                     user_profile["notifications_frequency"] = frequency_map[current_query]
#                     user.user_profile = user_profile
#                     await sync_to_async(user.save)()
#                     print("Updated user profile:", user.user_profile)

#                     if current_query == "daily_horoscope":
#                         response = "You'll receive daily horoscope updates. You can change this preference anytime."
#                     elif current_query == "weekly_horoscope":
#                         response = "You'll receive weekly horoscope updates. You can change this preference anytime."
#                     else:
#                         response = "You won't receive any horoscope notifications. You can change this preference anytime."
#                     await sync_to_async(send_text_message)(chat_id, response)

#                 except User.DoesNotExist:
#                     logger.error(f"User {chat_id} not found when trying to update notification preferences")
#                     await sync_to_async(send_text_message)(
#                         chat_id, "Sorry, there was an error updating your preferences. Please try again later."
#                     )
#                 except Exception as e:
#                     logger.error(f"Error updating user preferences: {str(e)}")
#                     await sync_to_async(send_text_message)(
#                         chat_id, "Sorry, there was an error updating your preferences. Please try again later."
#                     )
#                 initial_end = time.time()
#                 if settings.LOAD_TEST_MODE:
#                     await sync_to_async(log_time_to_csv)(
#                         chat_id, message_type, msg_id, "initial",
#                         initial_end - request_start_time
#                     )
            
#             else:
#                 await sync_to_async(send_text_message)(
#                     chat_id, f"Processing your request: {current_query}..."
#                 )
#                 initial_end = time.time()
#                 if settings.LOAD_TEST_MODE:
#                     await sync_to_async(log_time_to_csv)(
#                         chat_id, message_type, msg_id, "initial",
#                         initial_end - request_start_time
#                     )
#                 langraph_start = time.time()
#                 response = await run_llm_pipeline(  # Assuming this is made async
#                     current_query, memory=memory, platform="telegram",
#                     chat_id=chat_id, message_id=msg_id, user_message_type='text'
#                 )
#                 langraph_end = time.time()
#                 if settings.LOAD_TEST_MODE and response:
#                     await sync_to_async(log_time_to_csv)(
#                         chat_id, "text", msg_id, "langraph_pipeline_time",
#                         langraph_end - langraph_start
#                     )
#                 await sync_to_async(send_text_message)(chat_id, response)
                
#             response_end = time.time()
#             if settings.LOAD_TEST_MODE:
#                 await sync_to_async(log_time_to_csv)(
#                     chat_id, message_type, msg_id, "processing",
#                     response_end - request_start_time
#                 )

#         return JsonResponse({"status": "ok"}, status=200)

#     except json.JSONDecodeError as e:
#         logger.error(f"Failed to parse JSON: {e}")
#         return JsonResponse({"error": "Invalid JSON"}, status=400)
    
#     finally:
#         await sync_to_async(connection.close)()

