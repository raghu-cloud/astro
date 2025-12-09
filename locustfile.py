from locust import events
from locust.argument_parser import LocustArgumentParser
from locust import HttpUser, task, between, tag
import json
import time
import random
import uuid
import os
import sys
from dotenv import load_dotenv
from faker import Faker
import django
from itertools import cycle
import logging
from timing_test_csv_utils import average_api_time, average_non_api_time


# # Add project root to sys.path
# PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(0, PROJECT_ROOT)
final_user_count = 0 

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "My_AI_Guruji.settings")
django.setup()


from langchain_agent.models import User
from telegram_interface.models import TestTime

logger = logging.getLogger(__name__)  # Use this instead of stats_logger


load_dotenv()

fake = Faker()

KUNDLI_CHAT_IDS = list(
    User.objects.exclude(kundli_details__isnull=True)
                .exclude(kundli_details={})
                .values_list("id", flat=True)
)
print("Length of chat_ids with kundli json data", len(KUNDLI_CHAT_IDS))

random.shuffle(KUNDLI_CHAT_IDS)
chat_id_cycle = cycle(KUNDLI_CHAT_IDS)

with open("voice_file_ids.json", "r") as f:
    FILE_IDS = list(json.load(f).values())  # Just grab the list of file_ids



@events.init_command_line_parser.add_listener
def _(parser: LocustArgumentParser):
    parser.add_argument(
        "--test-type",
        choices=["all", "simple", "horoscope", "kundli", "voice", "kundli-followup"],
        default="all",
        help="Choose which test(s) to run"
    )


@events.spawning_complete.add_listener
def on_spawning_complete(user_count, **kwargs):
    global final_user_count
    final_user_count = user_count
    print("✔️ Final user count after all users spawned:", final_user_count)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    selected_category = environment.parsed_options.test_type 
    print("SELECTED CATEGORY:",selected_category)

    time.sleep(3)
    api_time = average_api_time()
    non_api_time = average_non_api_time()
    # user_count = environment.runner.user_count if environment.runner else 0
    # print("USER COUNT:", user_count)
    global final_user_count
    user_count = final_user_count
    print("FINAL USER COUNT:", user_count)

    # Save to DB
    TestTime.objects.create(
        category=selected_category,
        avg_api_time=api_time,
        avg_non_api_time=non_api_time,
        user_count=user_count,
    )

    print(f" Saved test results for category '{selected_category}' to DB.")



class TelegramUser(HttpUser):
    wait_time = between(2, 4)

    def on_start(self):
        self.chat_id = random.randint(100000, 999999) 
        self.headers = {
            "X-Telegram-Bot-Api-Secret-Token": os.getenv("TELEGRAM_WEBHOOK_SECRET_TOKEN")
        }

        file = "timing_logs.csv"
        if os.path.exists(file):
            os.remove(file)
        self.full_name = fake.name()
        self.gender = random.choice(["male", "female"])
        birthdate = fake.date_of_birth(minimum_age=18, maximum_age=60)
        self.day = birthdate.day
        self.month = birthdate.month
        self.year = birthdate.year

        birth_time = fake.time_object()
        self.hour = birth_time.hour
        self.minute = birth_time.minute
        self.second = birth_time.second

        self.place = fake.city()
    
    @tag("simple")
    @task
    def send_text_message(self):
        if self.environment.parsed_options.test_type not in ["simple", "all"]:
            return
        message_id = str(uuid.uuid4().int)[:9]

        messages = [
            "Hello AstroBot!",
            "Can you tell me about my future?",
            "What's my horoscope today?",
            "Tell me something interesting.",
            "I'm curious about astrology.",
            "Good morning AstroBot!",
            "What services do you provide?",
            "Hi there!"
        ]

        payload = {
            "message": {
                "chat": {"id": self.chat_id},  # Use same chat_id per user
                "message_id": int(message_id),
                "text": random.choice(messages)
            }
        }

        self.client.post("/api/telegram-webhook", json=payload, headers=self.headers)

    @tag("horoscope")
    @task
    def send_horoscope_request(self):
        if self.environment.parsed_options.test_type not in ["horoscope", "all"]:
            return

        message_id = str(uuid.uuid4().int)[:9]
        horoscope_type = random.choice(["daily horoscope", "weekly horoscope"])

        text = (
            f"Full Name: {self.full_name}\n"
            f"Birthdate: {self.day:02d}-{self.month:02d}-{self.year}\n"
            f"Time of Birth: {self.hour:02d}:{self.minute:02d}:{self.second:02d}\n"
            f"Generate {horoscope_type}"
        )

        payload = {
            "message": {
                "chat": {"id": self.chat_id},
                "message_id": int(message_id),
                "text": text
            }
        }
        self.client.post("/api/telegram-webhook", json=payload, headers=self.headers)

    @tag("kundli")
    @task
    def send_kundli_request(self):
        if self.environment.parsed_options.test_type not in ["kundli", "all"]:
            return
        message_id = str(uuid.uuid4().int)[:9]
        text = (
        f"Full Name: {self.full_name}\n"
        f"Gender: {self.gender}\n"
        f"Birthdate: {self.day:02d}-{self.month:02d}-{self.year}\n"
        f"Time of Birth: {self.hour:02d}:{self.minute:02d}:{self.second:02d}\n"
        f"Place of Birth: {self.place}\n"
        f"Generate Kundli"
        )

        payload = {
            "message": {
                "chat": {"id": self.chat_id},
                "message_id": int(message_id),
                "text": text
            }
        }
        self.client.post("/api/telegram-webhook", json=payload, headers=self.headers)


    @tag("voice")
    @task
    def send_voice_message(self):
        if self.environment.parsed_options.test_type not in ["voice", "all"]:
            return
        message_id = str(uuid.uuid4().int)[:9]
        file_id = random.choice(FILE_IDS)

        payload = {
            "message": {
                "chat": {"id": self.chat_id},
                "message_id": int(message_id),
                "voice": {
                    "file_id": file_id,
                    "mime_type": "audio/ogg",
                }
            }
        }

        self.client.post("/api/telegram-webhook", json=payload, headers=self.headers)

    
    @tag("kundli-followup")
    @task
    def send_kundli_followup_question(self):
        if self.environment.parsed_options.test_type not in ["kundli-followup", "all"]:
            return
        
        if not KUNDLI_CHAT_IDS:
            return  # Prevent failure if list is empty

        message_id = str(uuid.uuid4().int)[:9]
        chat_id = next(chat_id_cycle)

        followup_questions = [
            "What are my dashas?",
            "Do I have any doshas?",
            "Can you explain my planetary periods?",
            "What does my current dasha say?",
            "Are there any yogas in my chart?",
        ]

        payload = {
            "message": {
                "chat": {"id": chat_id},
                "message_id": int(message_id),
                "text": random.choice(followup_questions)
            }
        }

        self.client.post("/api/telegram-webhook", json=payload, headers=self.headers)

    
