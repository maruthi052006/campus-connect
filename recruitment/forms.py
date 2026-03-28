from django import forms
from .models import RecruitmentPost

class RecruitmentPostForm(forms.ModelForm):
    class Meta:
        model = RecruitmentPost
        fields = ['organization', 'title', 'description', 'required_skills', 'deadline']
        widgets = {
            'organization': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Job/Role Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'required_skills': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
