from django import forms
from .models import SkillExchangeRequest

class NewExchangeRequestForm(forms.ModelForm):
    class Meta:
        model = SkillExchangeRequest
        fields = ['receiver', 'offered_skills', 'requested_skills', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write a short message to explain your exchange offer...'}),
            'receiver': forms.Select(attrs={'class': 'form-control'}),
            'offered_skills': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'requested_skills': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }
