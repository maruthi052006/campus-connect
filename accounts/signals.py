from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        # Create Welcome notification
        try:
            from notifications.models import Notification
            if hasattr(Notification, 'objects'):
                Notification.objects.create(
                    recipient=instance,
                    notif_type='welcome'
                )
        except (ImportError, AttributeError):
            pass # Notification model not ready yet in this module
        
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
