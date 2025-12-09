from django.urls import path
# from .views import WhatsAppWebhook
from .api import api

urlpatterns = [
    # path('whatsapp-webhook/', WhatsAppWebhook.as_view(), name='whatsapp_webhook'),
    path('api/', api.urls),
]