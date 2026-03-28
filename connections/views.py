import json
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Q
from .models import Follow, ConnectionRequest, Connection
from .utils import get_connection_status, get_suggested_users
from django.contrib.auth import get_user_model

User = get_user_model()

class ConnectionsView(LoginRequiredMixin, TemplateView):
    template_name = 'connections.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['following'] = Follow.objects.filter(follower=user).select_related('following')
        context['followers'] = Follow.objects.filter(following=user).select_related('follower')
        
        # Add state IDs for checking relationships
        context['following_ids'] = list(context['following'].values_list('following_id', flat=True))
        
        conns = Connection.objects.filter(Q(user1=user) | Q(user2=user)).select_related('user1', 'user2')
        context['connections'] = [c.get_other_user(user) for c in conns]
        context['connection_ids'] = [u.id for u in context['connections']]
        
        context['pending_sent_ids'] = list(ConnectionRequest.objects.filter(sender=user, status='pending').values_list('receiver_id', flat=True))
        context['pending_received_ids'] = list(ConnectionRequest.objects.filter(receiver=user, status='pending').values_list('sender_id', flat=True))
        
        context['suggested'] = get_suggested_users(user)
        return context

class RequestsView(LoginRequiredMixin, TemplateView):
    template_name = 'requests.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['incoming'] = ConnectionRequest.objects.filter(receiver=user, status='pending').select_related('sender')
        context['outgoing'] = ConnectionRequest.objects.filter(sender=user, status='pending').select_related('receiver')
        return context

class FollowToggleAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            target_id = data.get('user_id')
            target_user = get_object_or_404(User, id=target_id)
            
            if target_user == request.user:
                return JsonResponse({'status': 'error', 'message': "Cannot follow yourself"}, status=400)
                
            follow, created = Follow.objects.get_or_create(follower=request.user, following=target_user)
            if not created:
                follow.delete()
                following = False
            else:
                following = True
                try:
                    from notifications.utils import notify_follow
                    notify_follow(request.user, target_user)
                except ImportError:
                    pass
            
            count = Follow.objects.filter(following=target_user).count()
            return JsonResponse({'following': following, 'count': count, 'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class SendConnectionRequestAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            target_id = data.get('user_id')
            target_user = get_object_or_404(User, id=target_id)
            
            if target_user == request.user:
                return JsonResponse({'status': 'error', 'message': "Cannot request yourself"}, status=400)
                
            req, created = ConnectionRequest.objects.get_or_create(sender=request.user, receiver=target_user)
            req.status = 'pending'
            req.save()
            
            try:
                from notifications.utils import notify_connect_request
                notify_connect_request(request.user, target_user)
            except ImportError:
                pass
                
            return JsonResponse({'status': 'success', 'message': 'Request sent'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class AcceptRequestAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            req_id = data.get('request_id')
            conn_req = get_object_or_404(ConnectionRequest, id=req_id, receiver=request.user, status='pending')
            
            # Clear ALL pending requests between these two users
            ConnectionRequest.objects.filter(
                (Q(sender=conn_req.sender, receiver=conn_req.receiver) | 
                 Q(sender=conn_req.receiver, receiver=conn_req.sender)),
                status='pending'
            ).update(status='accepted')
            
            # Ensure connection exists (order-agnostic check)
            if not Connection.objects.filter(
                (Q(user1=conn_req.sender, user2=conn_req.receiver) | 
                 Q(user1=conn_req.receiver, user2=conn_req.sender))
            ).exists():
                Connection.objects.create(user1=conn_req.sender, user2=conn_req.receiver)
            
            # Create mutual follows
            Follow.objects.get_or_create(follower=conn_req.sender, following=conn_req.receiver)
            Follow.objects.get_or_create(follower=conn_req.receiver, following=conn_req.sender)
            
            try:
                from notifications.utils import notify_connect_accept
                # Note: sender of notification is the current user (receiver of the request)
                notify_connect_accept(request.user, conn_req.sender)
            except ImportError:
                pass
                
            return JsonResponse({'status': 'success', 'message': 'Request accepted'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class AcceptUserConnectionAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            target_user_id = data.get('user_id')
            conn_req = get_object_or_404(ConnectionRequest, sender_id=target_user_id, receiver=request.user, status='pending')
            
            # Clear ALL pending requests between these two users
            ConnectionRequest.objects.filter(
                (Q(sender=conn_req.sender, receiver=conn_req.receiver) | 
                 Q(sender=conn_req.receiver, receiver=conn_req.sender)),
                status='pending'
            ).update(status='accepted')
            
            # Ensure connection exists
            if not Connection.objects.filter(
                (Q(user1=conn_req.sender, user2=conn_req.receiver) | 
                 Q(user1=conn_req.receiver, user2=conn_req.sender))
            ).exists():
                Connection.objects.create(user1=conn_req.sender, user2=conn_req.receiver)
            
            # Mutual follows
            Follow.objects.get_or_create(follower=conn_req.sender, following=conn_req.receiver)
            Follow.objects.get_or_create(follower=conn_req.receiver, following=conn_req.sender)
            
            try:
                from notifications.utils import notify_connect_accept
                notify_connect_accept(request.user, conn_req.sender)
            except ImportError:
                pass
                
            return JsonResponse({'status': 'success', 'message': 'Connection accepted'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class RejectRequestAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            req_id = data.get('request_id')
            conn_req = get_object_or_404(ConnectionRequest, id=req_id, receiver=request.user, status='pending')
            
            conn_req.status = 'rejected'
            conn_req.save()
            return JsonResponse({'status': 'success', 'message': 'Request rejected'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class WithdrawRequestAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            req_id = data.get('request_id')
            conn_req = get_object_or_404(ConnectionRequest, id=req_id, sender=request.user, status='pending')
            
            conn_req.status = 'withdrawn'
            conn_req.save()
            return JsonResponse({'status': 'success', 'message': 'Request withdrawn'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class RemoveConnectionAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            target_user = get_object_or_404(User, id=user_id)
            
            Connection.objects.filter(Q(user1=request.user, user2=target_user) | Q(user1=target_user, user2=request.user)).delete()
            return JsonResponse({'status': 'success', 'message': 'Connection removed'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class SuggestedUsersAJAX(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            suggested_users = get_suggested_users(request.user)[:5] # Just top 5 for sidebar
            data = []
            for u in suggested_users:
                profile_pic = u.profile.profile_picture.url if u.profile.profile_picture else None
                data.append({
                    'id': u.id,
                    'full_name': u.full_name or u.username,
                    'username': u.username,
                    'role': u.role,
                    'department': u.department,
                    'profile_picture': profile_pic
                })
            return JsonResponse({'status': 'success', 'users': data})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
