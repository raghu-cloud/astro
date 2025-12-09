import requests
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SECRET_TOKEN = os.getenv("TELEGRAM_WEBHOOK_SECRET_TOKEN")



# TELEGRAM_BOT_TOKEN = "7875328837:AAGYr-6lbe0pUOwrFLsp0HXTTxQfn6bF0zg"

# TELEGRAM_BOT_TOKEN = "7816863946:AAEnMSsVctqrGJ3iq-JDEkBW-vjUXXYO9rs"
# TELEGRAM_BOT_TOKEN = "7875328837:AAGYr-6lbe0pUOwrFLsp0HXTTxQfn6bF0zg"


# SECRET_TOKEN='12345'
# print(SECRET_TOKEN)
# print(TELEGRAM_BOT_TOKEN)
# WEBHOOK_URL = "https://13shk1mg04.execute-api.ap-south-1.amazonaws.com/api/telegram-webhook"

SECRET_TOKEN='12345'
print(SECRET_TOKEN)
print(TELEGRAM_BOT_TOKEN)


WEBHOOK_URL = "https://a8c2eac06a36.ngrok-free.app/api/telegram-webhook"
# WEBHOOK_URL="https://aoek8g2pvg.execute-api.ap-south-1.amazonaws.com/api/telegram-webhook"
# WEBHOOK_URL = "https://3b0e-14-142-182-251.ngrok-free.app/api/telegram-webhook"
# WEBHOOK_URL='https://m60ig3k6w7.execute-api.ap-south-1.amazonaws.com/api/telegram-webhook'
# WEBHOOK_URL = "https://05d8-14-142-182-251.ngrok-free.app/api/telegram-webhook"
# WEBHOOK_URL = "https://3b0e-14-142-182-251.ngrok-free.app/api/telegram-webhook"





# WEBHOOK_URL = "https://c7d7-2402-e280-2130-9b-8066-61a0-b2aa-2f5f.ngrok-free.app/api/telegram-webhook"



# WEBHOOK_URL = "https://48e3-2401-4900-900f-49b1-d9b7-802a-39c-23fc.ngrok-free.app/api/telegram-webhook"

# WEBHOOK_URL = "https://2027-2401-4900-6310-367d-2c24-346a-1810-1695.ngrok-free.app/api/telegram-webhook"



#WEBHOOK_URL = "https://b954-49-207-192-40.ngrok-free.app/api/telegram-webhook"
# WEBHOOK_URL = "https://27ca-2402-e280-2130-9b-7895-fe05-9d21-be2e.ngrok-free.app/api/telegram-webhook"




# WEBHOOK_URL = "https://7442-2402-e280-2130-9b-5804-7b6e-feb5-e0a0.ngrok-free.app/api/telegram-webhook"






response = requests.post(
    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook",
    data={
        "url": WEBHOOK_URL,
        "secret_token": SECRET_TOKEN,
        "drop_pending_updates" : True,
    }
)

print(response.json())  # Check the response from Telegram