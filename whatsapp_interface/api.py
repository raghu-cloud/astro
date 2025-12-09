from ninja import NinjaAPI
from .views import verify_webhook, handle_message
from .decorators.security import signature_required

whatsapp_api = NinjaAPI(urls_namespace="whatsapp_api")

@whatsapp_api.get("/webhook")
def webhook_get(request):
    return verify_webhook(request)

@whatsapp_api.post("/webhook")
@signature_required
def webhook_post(request):
    return handle_message(request)