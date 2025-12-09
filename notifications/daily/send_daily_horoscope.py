### To send daily horoscope to users, who choose daily notifications as their perference in their user profile

import os
import django
import sys
import time
import logging
from datetime import datetime
from celery import shared_task

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('daily_horoscope.log')
    ]
)

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
parent_dir = os.path.dirname(project_root)

logging.info(f"Project root: {project_root}")
logging.info(f"Parent dir: {parent_dir}")

sys.path.insert(0, parent_dir)
sys.path.insert(0, project_root)

# Set up Django environment
logging.info("Setting up Django environment...")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'My_AI_Guruji.settings')
django.setup()
logging.info("Django environment setup complete")

from langchain_agent.models import User
from langchain_agent.utils import run_llm_pipeline
from telegram_interface.utils import send_text_message

@shared_task(bind=True)
def send_daily_horoscopes():
    """
    Fetches users with daily notifications and sends them their horoscope
    """
    logging.info("Starting to fetch users with daily notifications...")
    
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
                user_message_type='text'
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


if __name__ == "__main__":
    logging.info(f"Starting daily horoscope distribution at {datetime.now()}")
    try:
        send_daily_horoscopes()
        logging.info(f"Completed daily horoscope distribution at {datetime.now()}")
    except Exception as e:
        logging.error(f"Script failed with error: {str(e)}")
        logging.exception("Full traceback:") 
