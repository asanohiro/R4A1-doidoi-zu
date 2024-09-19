from django import forms
from .models import LostItem

class UploadImageForm(forms.ModelForm):
    class Meta:
        model = LostItem
        fields = ['image', 'description', 'location']
