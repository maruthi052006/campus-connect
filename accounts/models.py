from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    class RoleChoices(models.TextChoices):
        STUDENT = 'Student', _('Student')
        TEACHER = 'Teacher', _('Teacher')
        MANAGEMENT = 'Management', _('Management')
        ADMIN = 'Admin', _('Admin')

    class DepartmentChoices(models.TextChoices):
        AIDS = 'Artificial Intelligence & Data Science', _('Artificial Intelligence & Data Science')
        CIVIL = 'Civil Engineering', _('Civil Engineering')
        CSE = 'Computer Science & Engineering', _('Computer Science & Engineering')
        CSE_AIML = 'Computer Science and Engineering (Artificial Intelligence & Machine Learning)', _('Computer Science and Engineering (Artificial Intelligence & Machine Learning)')
        CSE_CS = 'Computer Science and Engineering (Cyber Security)', _('Computer Science and Engineering (Cyber Security)')
        EEE = 'Electrical & Electronics Engineering', _('Electrical & Electronics Engineering')
        ECE = 'Electronics & Communication Engineering', _('Electronics & Communication Engineering')
        ECE_VLSI = 'Electronics Engineering (VLSI Design and Technology)', _('Electronics Engineering (VLSI Design and Technology)')
        IT = 'Information Technology', _('Information Technology')
        MECH = 'Mechanical Engineering', _('Mechanical Engineering')
        MECHTRONICS = 'Mechatronics Engineering', _('Mechatronics Engineering')
        HUMANITIES = 'Science & Humanities', _('Science & Humanities')

    username = models.CharField(max_length=50, unique=True, help_text=_("Roll Number"))
    full_name = models.CharField(max_length=150, blank=True)
    
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.STUDENT
    )
    department = models.CharField(
        max_length=150, 
        choices=DepartmentChoices.choices, 
        blank=True
    )
    batch = models.CharField(max_length=4, blank=True)
    
    is_first_login = models.BooleanField(default=True)
    is_profile_setup = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} - {self.full_name}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    @property
    def get_avatar_url(self):
        try:
            if self.profile_picture and hasattr(self.profile_picture, 'url'):
                # Check if file actually exists if you want to be super safe, 
                # but usually .url is enough if it's set.
                return self.profile_picture.url
        except Exception:
            pass
        from django.templatetags.static import static
        return static('images/default-avatar.png')
    cover_photo = models.ImageField(upload_to='profiles/covers/', blank=True, null=True)
    bio = models.TextField(blank=True)
    domain = models.CharField(max_length=100, blank=True)
    linkedin_url = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    portfolio_url = models.URLField(blank=True, null=True)
    
    # Privacy Settings
    is_private = models.BooleanField(default=False)
    show_email = models.BooleanField(default=True)
    allow_connection_requests = models.BooleanField(default=True)
    
    # Notification Preferences
    notif_likes = models.BooleanField(default=True)
    notif_comments = models.BooleanField(default=True)
    notif_connections = models.BooleanField(default=True)
    notif_messages = models.BooleanField(default=True)
    notif_projects = models.BooleanField(default=True)
    notif_events = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class UserSkill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='skilling_users')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'skill')
        
    def __str__(self):
        return f"{self.user.username} - {self.skill.name}"
