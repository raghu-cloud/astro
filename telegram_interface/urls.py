from django.urls import path
from .api import telegram_api

urlpatterns = [
    path('api/', telegram_api.urls),
]