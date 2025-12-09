from ninja import NinjaAPI
from .decorators.security import telegram_token_required
from .views import handle_telegram_message
import os

telegram_api = NinjaAPI(urls_namespace="telegram_api")

@telegram_api.post("/telegram-webhook")
@telegram_token_required
def telegram_webhook(request):
    return handle_telegram_message(request)