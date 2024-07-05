from django.db import models

class LostItem(models.Model):
    image = models.ImageField(upload_to='images/')
    comment = models.TextField(blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
