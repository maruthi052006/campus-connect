from django.db.models import Count, Q
from .models import Connection, ConnectionRequest, Follow
from django.contrib.auth import get_user_model

User = get_user_model()

def get_connection_status(user1, user2):
    if user1 == user2:
        return 'self'
    
    # Check connection
    if Connection.objects.filter(Q(user1=user1, user2=user2) | Q(user1=user2, user2=user1)).exists():
        return 'connected'
        
    # Check pending sent requests
    if ConnectionRequest.objects.filter(sender=user1, receiver=user2, status='pending').exists():
        return 'pending_sent'
        
    # Check pending received requests
    if ConnectionRequest.objects.filter(sender=user2, receiver=user1, status='pending').exists():
        return 'pending_received'
        
    # Check if following
    if Follow.objects.filter(follower=user1, following=user2).exists():
        return 'following'
        
    return 'none'

def get_suggested_users(user):
    qs = User.objects.exclude(id=user.id)
    
    # Gather connected ids
    connected_users_qs = Connection.objects.filter(Q(user1=user) | Q(user2=user))
    connected_ids = set()
    for conn in connected_users_qs:
        connected_ids.add(conn.user1_id)
        connected_ids.add(conn.user2_id)
    
    qs = qs.exclude(id__in=connected_ids)
    
    # Gather pending request ids
    pending_sent = ConnectionRequest.objects.filter(sender=user, status='pending').values_list('receiver_id', flat=True)
    pending_received = ConnectionRequest.objects.filter(receiver=user, status='pending').values_list('sender_id', flat=True)
    qs = qs.exclude(id__in=pending_sent).exclude(id__in=pending_received)
    
    # Favor same department
    if user.department:
        qs = qs.filter(department=user.department)
        
    # Order by simple sum of their active connections
    qs = qs.annotate(total_connections=Count('connections_initiated') + Count('connections_received')).order_by('-total_connections')[:10]
    return qs
