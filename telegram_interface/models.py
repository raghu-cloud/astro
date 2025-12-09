from django.db import models

# Create your models here.

class TestTime(models.Model):
    category = models.CharField(max_length=50)
    avg_api_time = models.FloatField()
    avg_non_api_time = models.FloatField()
    user_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)