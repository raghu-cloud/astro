
import os
import django
import sys
import time
import logging
from datetime import datetime
from celery import shared_task
from langchain_agent.models import User
from langchain_agent.utils import run_llm_pipeline,run_llm_pipeline_notification
from telegram_interface.utils import send_text_message
from langgraph.graph.message import add_messages
from langchain_agent.utils import chatbot,tool_node,tool_node_1,store_in_db,after_horoscope,after_kundli,should_continue,route_decision,llm_call_2,llm_call_3,llm_call_4,vector_db_conversation
from langgraph.graph import StateGraph, START, END
from typing import Annotated,TypedDict
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver

class State(TypedDict):
    messages: Annotated[list, add_messages]
    decision: Annotated[list, add_messages]
    tool: Annotated[list, add_messages]
    user_message: Annotated[list, add_messages]
    dob: Annotated[list, add_messages]
    time: Annotated[list, add_messages]
    name: Annotated[list, add_messages]
    thread_id: str
    set: str
    message_id: str
    user_message_type: str
    pipeline_db_id:str



@shared_task()
def send_daily_horoscopes():
    """
    Fetches users with daily notifications and sends them their horoscope
    """
    logging.info("Starting to fetch users with daily notifications...")
    # graph_builder = StateGraph(State)
    # graph_builder.add_node("chatbot", chatbot)
    # graph_builder.add_node("tools", tool_node)
    # graph_builder.add_node("tools_1", tool_node_1)
    # graph_builder.add_node("store_in_db", store_in_db)
    # graph_builder.add_node("after_kundli", after_kundli)
    # graph_builder.add_node("after_horoscope", after_horoscope)
    # graph_builder.add_conditional_edges(
    #     "llm_call_4", should_continue, {"tools": "tools_1", "store_in_db": "store_in_db"}
    # )
    # graph_builder.add_conditional_edges("llm_call_3", should_continue, {"tools": "tools", "store_in_db": "store_in_db"})
    # graph_builder.add_conditional_edges(
    #     "chatbot",
    #     route_decision,
    #     {  # Name returned by route_decision : Name of next node to visit
    #         "llm_call_2": "llm_call_2",
    #         "llm_call_3": "llm_call_3",
    #         "llm_call_4": "llm_call_4",
    #         "vector_db": "vector_db",
    #     },
    # )
    # graph_builder.add_node("llm_call_2", llm_call_2)
    # graph_builder.add_node("llm_call_3", llm_call_3)
    # graph_builder.add_node("llm_call_4", llm_call_4)
    # graph_builder.add_node("vector_db", vector_db_conversation)
    # graph_builder.add_edge("llm_call_2", "store_in_db")
    # # graph_builder.add_edge("llm_call_3", "store_in_db")
    # # graph_builder.add_edge("llm_call_4", "store_in_db")
    # graph_builder.add_edge("vector_db", "store_in_db")
    # graph_builder.add_edge("tools", "after_horoscope")
    # graph_builder.add_edge("store_in_db", END)
    # graph_builder.add_edge("tools_1", "after_kundli")
    # graph_builder.add_edge("after_kundli", "store_in_db")
    # graph_builder.add_edge("after_horoscope", "store_in_db")

    # graph_builder.add_edge(START, "chatbot")

    # DB_URI = os.getenv('DB_URI')
    # connection_kwargs = {
    #     "autocommit": True,
    #     "prepare_threshold": 0,
    # }

    # shared_pool =ConnectionPool(
    #     conninfo=DB_URI,
    #     max_size=100,  # Set according to your DB server limits
    #     kwargs=connection_kwargs
    # )

    # # ✅ Global checkpointer (uses shared pool)
    # checkpointer = PostgresSaver(shared_pool)
    # checkpointer.setup() 
    # graph = graph_builder.compile(checkpointer=checkpointer)

    
    # Query users where user_profile contains notifications_frequency = 'daily'
    daily_users = User.objects.filter(user_profile__notifications_frequency='daily')
    
    logging.info(f"Found {daily_users.count()} users with daily notifications")
    
    for user in daily_users:
        try:
            logging.info(f"\nProcessing user {user.id}")
            
            # Generate horoscope using the LLM pipeline
            logging.info(f"Generating horoscope for user {user.id}...")
            response = run_llm_pipeline(
                "daily horoscope",
                memory=None,
                platform="telegram",
                chat_id=user.id,
                message_id=None,
                user_message_type='text',
   
            )
            
            if response:
                logging.info(f"Successfully generated horoscope for user {user.id}")
                # Send the daily horoscope to the user
                logging.info(f"Sending horoscope to user {user.id}...")
                send_text_message(user.id, "Your Daily Horoscope is ready")
                send_text_message(user.id, response)
                logging.info(f"Successfully sent horoscope to user {user.id}")
            else:
                logging.error(f"Failed to generate horoscope for user {user.id}")
                
        except Exception as e:
            logging.error(f"Error processing user {user.id}: {str(e)}")
            logging.exception("Full traceback:")


def send_weekly_horoscopes():
    """
    Fetches users with weekly notifications and sends them their horoscope
    """
    
    # Query users where user_profile comtains notifications_frequency = 'weekly'
    weekly_users = User.objects.filter(user_profile__notifications_frequency='weekly')
    
    print(f"Found {weekly_users.count()} users with weekly notifications")
    
    for user in weekly_users:
        try:
            print(f"\nProcessing user {user.id}")
            
            # Generate horoscope using the LLM pipeline
            response = run_llm_pipeline(
                "weekly horoscope",
                memory=None,
                platform="telegram",
                chat_id=user.id,
                message_id=None,
                user_message_type='text'
            )
            
            if response:
                # Send the weekly horoscope to the user
                send_text_message(user.id, "Your Weekly Horoscope is ready")
                send_text_message(user.id, response)
                logging.info(f"Successfully sent horoscope to user {user.id}")
            else:
                logging.info(f"Failed to generate horoscope for user {user.id}")
                
        except Exception as e:
            logging.info(f"Error processing user {user.id}: {str(e)}")
