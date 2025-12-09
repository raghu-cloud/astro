### To send weekly horoscope to users, who choose weekly notifications as their perference in their user profile

import os
import django
import sys
import time
import logging
from datetime import datetime


project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
parent_dir = os.path.dirname(project_root)

sys.path.insert(0, parent_dir)
sys.path.insert(0, project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'My_AI_Guruji.settings')
django.setup()


from langchain_agent.models import User
from langchain_agent.utils import run_llm_pipeline
from telegram_interface.utils import send_text_message


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


if __name__ == "__main__":
    logging.info(f"Starting weekly horoscope distribution at {datetime.now()}")
    send_weekly_horoscopes()
    logging.info(f"Completed weekly horoscope distribution at {datetime.now()}") 
