from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, SetPasswordForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re
from .models import Profile, Skill, UserSkill

User = get_user_model()

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(label="Roll Number", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Roll Number'}))
    password = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class ForcePasswordChangeForm(SetPasswordForm):
    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'[A-Za-z]', password):
            raise ValidationError("Password must contain at least one letter.")
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain at least one number.")
        return password

class ProfileSetupForm(forms.ModelForm):
    full_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    department = forms.ChoiceField(choices=User.DepartmentChoices.choices, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    batch = forms.CharField(max_length=4, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Profile
        fields = ['profile_picture', 'bio', 'domain', 'linkedin_url', 'github_url', 'portfolio_url']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'domain': forms.TextInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'github_url': forms.URLInput(attrs={'class': 'form-control'}),
            'portfolio_url': forms.URLInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ProfileSetupForm, self).__init__(*args, **kwargs)
        if self.user:
            self.fields['full_name'].initial = self.user.full_name
            self.fields['department'].initial = self.user.department
            self.fields['batch'].initial = self.user.batch

    def save(self, commit=True):
        profile = super(ProfileSetupForm, self).save(commit=False)
        if self.user:
            self.user.full_name = self.cleaned_data['full_name']
            self.user.department = self.cleaned_data['department']
            self.user.batch = self.cleaned_data['batch']
            if commit:
                self.user.save()
                profile.save()
        return profile

class EditProfileForm(forms.ModelForm):
    full_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    department = forms.ChoiceField(choices=User.DepartmentChoices.choices, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    batch = forms.CharField(max_length=4, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(choices=[('Student', 'Student'), ('Teacher/Faculty', 'Teacher/Faculty')], required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    
    class Meta:
        model = Profile
        fields = ['profile_picture', 'cover_photo', 'bio', 'domain', 'linkedin_url', 'github_url', 'portfolio_url']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'domain': forms.TextInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'github_url': forms.URLInput(attrs={'class': 'form-control'}),
            'portfolio_url': forms.URLInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(EditProfileForm, self).__init__(*args, **kwargs)
        if self.user:
            self.fields['full_name'].initial = self.user.full_name
            self.fields['department'].initial = self.user.department
            self.fields['batch'].initial = self.user.batch
            self.fields['role'].initial = self.user.role

    def save(self, commit=True):
        profile = super(EditProfileForm, self).save(commit=commit)
        if self.user:
            self.user.full_name = self.cleaned_data['full_name']
            self.user.department = self.cleaned_data['department']
            self.user.batch = self.cleaned_data['batch']
            if self.cleaned_data.get('role'):
                self.user.role = self.cleaned_data['role']
            if commit:
                self.user.save()
        return profile

class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['name']

from django.core.validators import FileExtensionValidator

class AddUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'role', 'department', 'batch']
        labels = {'username': 'Roll Number'}
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'batch': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        validators=[FileExtensionValidator(['csv'])],
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )
