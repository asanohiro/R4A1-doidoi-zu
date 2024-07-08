# app/models.py
from django.db import models

class LostItem(models.Model):
    image = models.ImageField(upload_to='images/')
    comment = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    date_time = models.DateTimeField(auto_now_add=True)
