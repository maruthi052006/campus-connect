from django import forms
from .models import Project

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'tech_stack', 'github_url', 'live_url', 'thumbnail']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Explain what this project does...'}),
            'tech_stack': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'github_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/...'}),
            'live_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
        }
