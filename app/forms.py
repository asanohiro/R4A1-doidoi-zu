from django import forms
from .models import LostItem

class UploadImageForm(forms.ModelForm):
    class Meta:
        model = LostItem
        fields = ['image', 'location']
        widgets = {
            'location': forms.HiddenInput(),
        }
