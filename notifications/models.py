from django.db import models
from django.contrib.auth import get_user_model
from feed.models import Post
from organizations.models import Organization
from django.urls import reverse
from django.apps import apps

User = get_user_model()

class Notification(models.Model):
    TYPE_CHOICES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
        ('connect_request', 'Connection Request'),
        ('connect_accept', 'Connection Accept'),
        ('skill_exchange', 'Skill Exchange'),
        ('exchange_message', 'Exchange Message'),
        ('new_post', 'New Post'),
        ('org_join', 'Organization Join'),
        ('org_accept', 'Organization Accept'),
        ('welcome', 'Welcome'),
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_notifications')
    notif_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.TextField(blank=True)
    related_post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    related_org = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)
    related_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications_target')
    related_session = models.ForeignKey('skills.SkillExchangeSession', on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.message:
            self.message = self.generate_message()
        super().save(*args, **kwargs)

    def generate_message(self):
        sender_name = self.sender.full_name if self.sender and self.sender.full_name else (self.sender.username if self.sender else "System")
        
        if self.notif_type == 'like':
            return f"{sender_name} liked your post."
        elif self.notif_type == 'comment':
            return f"{sender_name} commented on your post."
        elif self.notif_type == 'follow':
            return f"{sender_name} started following you."
        elif self.notif_type == 'connect_request':
            return f"{sender_name} sent you a connection request."
        elif self.notif_type == 'connect_accept':
            return f"{sender_name} accepted your connection request."
        elif self.notif_type == 'skill_exchange':
            return f"{sender_name} requested a skill exchange."
        elif self.notif_type == 'org_join':
            return f"{sender_name} requested to join {self.related_org.name if self.related_org else 'your organization'}."
        elif self.notif_type == 'exchange_message':
            return f"{sender_name} sent you a message in the skill exchange."
        elif self.notif_type == 'new_post':
            return f"{sender_name} shared a new post."
        elif self.notif_type == 'org_accept':
            return f"Your request to join {self.related_org.name if self.related_org else 'an organization'} was accepted."
        elif self.notif_type == 'welcome':
            return "Welcome to CampusConnect! Complete your profile to get started."
        return "You have a new notification."

    def get_url(self):
        if self.notif_type in ['like', 'comment', 'new_post'] and self.related_post:
            return reverse('feed:home') + f"#post-{self.related_post.id}"
        elif self.notif_type in ['follow', 'connect_request', 'connect_accept'] and self.related_user:
            return reverse('accounts:user_profile', kwargs={'username': self.related_user.username})
        elif self.notif_type == 'skill_exchange':
            return reverse('skills:skill_exchange')
        elif self.notif_type == 'exchange_message' and self.related_session:
            return reverse('skills:exchange_chat', kwargs={'session_id': self.related_session.id})
        elif self.notif_type in ['org_join', 'org_accept'] and self.related_org:
            return reverse('organizations:org_profile', kwargs={'slug': self.related_org.slug})
        return "#"

    def __str__(self):
        return f"To {self.recipient.username}: {self.message}"
