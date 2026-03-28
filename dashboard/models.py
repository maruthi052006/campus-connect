from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ProfileViewTracker(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_views_received')
    viewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='profiles_viewed')
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} viewed by {self.viewer.username if self.viewer else 'Anonymous'}"
