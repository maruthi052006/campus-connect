from .models import Notification

def notify_like(sender, post):
    if sender != post.author:
        Notification.objects.create(
            recipient=post.author,
            sender=sender,
            notif_type='like',
            related_post=post
        )

def notify_comment(sender, post):
    if sender != post.author:
        Notification.objects.create(
            recipient=post.author,
            sender=sender,
            notif_type='comment',
            related_post=post
        )

def notify_follow(sender, receiver):
    if sender != receiver:
        Notification.objects.create(
            recipient=receiver,
            sender=sender,
            notif_type='follow',
            related_user=sender
        )

def notify_connect_request(sender, receiver):
    if sender != receiver:
        Notification.objects.create(
            recipient=receiver,
            sender=sender,
            notif_type='connect_request',
            related_user=sender
        )

def notify_connect_accept(sender, receiver):
    if sender != receiver:
        Notification.objects.create(
            recipient=receiver,
            sender=sender,
            notif_type='connect_accept',
            related_user=sender
        )

def notify_skill_exchange(sender, receiver):
    if sender != receiver:
        Notification.objects.create(
            recipient=receiver,
            sender=sender,
            notif_type='skill_exchange'
        )

def notify_skill_exchange_accept(sender, receiver):
    if sender != receiver:
        Notification.objects.create(
            recipient=receiver,
            sender=sender,
            notif_type='skill_exchange_accept'
        )

def notify_skill_exchange_complete(sender, receiver):
    if sender != receiver:
        Notification.objects.create(
            recipient=receiver,
            sender=sender,
            notif_type='skill_exchange_complete'
        )

def notify_org_join(user, org):
    from organizations.models import OrganizationMember
    admins = OrganizationMember.objects.filter(organization=org, role='Admin')
    for admin in admins:
        if admin.user != user:
            Notification.objects.create(
                recipient=admin.user,
                sender=user,
                notif_type='org_join',
                related_org=org
            )

def notify_org_accept(user, org):
    Notification.objects.create(
        recipient=user,
        notif_type='org_accept',
        related_org=org
    )

def notify_exchange_message(sender, session):
    recipient = session.exchange_request.sender if sender == session.exchange_request.receiver else session.exchange_request.receiver
    Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notif_type='exchange_message',
        related_session=session
    )

def notify_new_post(post):
    from connections.models import Follow, Connection
    user = post.author
    
    # Get followers
    followers = Follow.objects.filter(following=user).values_list('follower', flat=True)
    
    # Get connections
    conn1 = Connection.objects.filter(user1=user).values_list('user2', flat=True)
    conn2 = Connection.objects.filter(user2=user).values_list('user1', flat=True)
    
    recipient_ids = set(followers) | set(conn1) | set(conn2)
    
    notifications = [
        Notification(
            recipient_id=rid,
            sender=user,
            notif_type='new_post',
            related_post=post
        ) for rid in recipient_ids if rid != user.id
    ]
    
    Notification.objects.bulk_create(notifications)
