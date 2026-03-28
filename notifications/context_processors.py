def notifications(request):
    if request.user.is_authenticated:
        try:
            from notifications.models import Notification
            count = Notification.objects.filter(recipient=request.user, is_read=False).count()
            return {'unread_notifications_count': count}
        except ImportError:
            return {'unread_notifications_count': 0}
    return {'unread_notifications_count': 0}
