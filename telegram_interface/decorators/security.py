from django.http import HttpResponse
from functools import wraps
from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_SECRET_TOKEN = os.getenv("TELEGRAM_WEBHOOK_SECRET_TOKEN")

def telegram_token_required(view_func):
    """
    Decorator to verify the Telegram secret token in the request headers.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Get the secret token from the request headers
        print(request)
        secret_token = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
        print(f"Received Token: {secret_token}")
        print(f"Expected Token: {TELEGRAM_SECRET_TOKEN}")
        
        # Verify the token
        if secret_token != TELEGRAM_SECRET_TOKEN:
            return HttpResponse('Unauthorized', status=401)
        
        # If the token is valid, call the original view function
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view