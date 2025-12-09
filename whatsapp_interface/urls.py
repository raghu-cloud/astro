from django.urls import path
from .api import whatsapp_api

urlpatterns = [
    path('api/', whatsapp_api.urls),
]