from functools import wraps
from django.http import JsonResponse
import hmac
import os
import hashlib
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()
WHATSAPP_SECRET_KEY = os.getenv("APP_SECRET")

def signature_required(view_func):
    """Verifies the X-Hub-Signature-256 header sent by WhatsApp."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        signature = request.headers.get("X-Hub-Signature-256")
        if not signature:
            return JsonResponse({"error": "Signature missing"}, status=400)

        payload = request.body
        secret = WHATSAPP_SECRET_KEY.encode()
        expected_signature = "sha256=" + hmac.new(secret, payload, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_signature, signature):
            return JsonResponse({"error": "Invalid signature"}, status=403)

        return view_func(request, *args, **kwargs)
    return _wrapped_view
