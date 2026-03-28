from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import Skill # Assuming Skill is in accounts

User = get_user_model()

class SkillExchangeRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_skill_exchanges')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_skill_exchanges')
    offered_skills = models.ManyToManyField(Skill, related_name='offered_in_exchanges')
    requested_skills = models.ManyToManyField(Skill, related_name='requested_in_exchanges')
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Exchange: {self.sender.username} -> {self.receiver.username} ({self.status})"

class SkillExchangeSession(models.Model):
    exchange_request = models.OneToOneField(SkillExchangeRequest, on_delete=models.CASCADE, related_name='session')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Session for {self.exchange_request}"

class SkillExchangeMessage(models.Model):
    session = models.ForeignKey(SkillExchangeSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_exchange_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Msg from {self.sender.username} at {self.timestamp}"
