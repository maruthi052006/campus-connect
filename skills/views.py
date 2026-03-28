import json
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, View, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Q
from .models import SkillExchangeRequest, SkillExchangeSession, SkillExchangeMessage
from .forms import NewExchangeRequestForm
from django.utils import timezone
from accounts.models import Skill, User

class SkillExchangeDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'skill_exchange.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['received'] = SkillExchangeRequest.objects.filter(receiver=user, status='pending').order_by('-created_at')
        context['sent'] = SkillExchangeRequest.objects.filter(sender=user, status='pending').order_by('-created_at')
        
        active_requests = SkillExchangeRequest.objects.filter(
            Q(sender=user) | Q(receiver=user), 
            status='active'
        ).select_related('session').order_by('-created_at')
        
        context['active'] = active_requests
        context['completed'] = SkillExchangeRequest.objects.filter(
            Q(sender=user) | Q(receiver=user),
            status='completed'
        ).order_by('-created_at')
        context['form'] = NewExchangeRequestForm() # for the modal
        return context

class NewExchangeRequestView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = NewExchangeRequestForm(request.POST)
        if form.is_valid():
            exchange = form.save(commit=False)
            exchange.sender = request.user
            
            if exchange.receiver == request.user:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('accept') == 'application/json':
                    return JsonResponse({'status': 'error', 'message': "Cannot exchange with yourself"}, status=400)
                return redirect('skills:skill_exchange')
                    
            exchange.status = 'pending'
            exchange.save()
            form.save_m2m() # Save ManyToMany skills
            
            try:
                from notifications.utils import notify_skill_exchange
                notify_skill_exchange(request.user, exchange.receiver)
            except ImportError:
                pass
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('accept') == 'application/json':
                return JsonResponse({'status': 'success', 'message': 'Exchange Request Sent'})
            return redirect('skills:skill_exchange')
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('accept') == 'application/json':
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
        return redirect('skills:skill_exchange')

class AcceptExchangeAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            req_id = data.get('request_id')
            exchange = get_object_or_404(SkillExchangeRequest, id=req_id, receiver=request.user, status='pending')
            
            exchange.status = 'active'
            exchange.save()
            
            SkillExchangeSession.objects.create(exchange_request=exchange)
            
            try:
                from notifications.utils import notify_skill_exchange_accept
                notify_skill_exchange_accept(request.user, exchange.sender)
            except ImportError:
                pass
                
            return JsonResponse({'status': 'success', 'message': 'Exchange Accepted'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class RejectExchangeAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            req_id = data.get('request_id')
            exchange = get_object_or_404(SkillExchangeRequest, id=req_id, receiver=request.user, status='pending')
            
            exchange.status = 'rejected'
            exchange.save()
            return JsonResponse({'status': 'success', 'message': 'Exchange Rejected'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class WithdrawExchangeAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            req_id = data.get('request_id')
            exchange = get_object_or_404(SkillExchangeRequest, id=req_id, sender=request.user, status='pending')
            
            exchange.status = 'withdrawn'
            exchange.save()
            return JsonResponse({'status': 'success', 'message': 'Exchange Withdrawn'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class CompleteExchangeAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            req_id = data.get('request_id')
            exchange = get_object_or_404(SkillExchangeRequest, id=req_id, status='active')
            
            if request.user != exchange.sender and request.user != exchange.receiver:
                return JsonResponse({'status': 'error', 'message': 'Not authorized'}, status=403)
                
            exchange.status = 'completed'
            exchange.save()
            
            session = exchange.session
            session.completed_at = timezone.now()
            session.save()
            
            try:
                from notifications.utils import notify_skill_exchange_complete
                other_user = exchange.sender if request.user == exchange.receiver else exchange.receiver
                notify_skill_exchange_complete(request.user, other_user)
            except ImportError:
                pass
            
            return JsonResponse({'status': 'success', 'message': 'Exchange Completed'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class SkillExchangeChatView(LoginRequiredMixin, DetailView):
    model = SkillExchangeSession
    template_name = 'skill_exchange_chat.html'
    context_object_name = 'session'

    def get_object(self, queryset=None):
        session = get_object_or_404(SkillExchangeSession, id=self.kwargs.get('session_id'))
        if self.request.user != session.exchange_request.sender and self.request.user != session.exchange_request.receiver:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return session

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = self.get_object()
        context['chat_messages'] = session.messages.all().select_related('sender')
        context['partner'] = session.exchange_request.sender if self.request.user == session.exchange_request.receiver else session.exchange_request.receiver
        
        # Mark messages as read
        session.messages.filter(is_read=False).exclude(sender=self.request.user).update(is_read=True)
        
        # Other active exchanges for sidebar
        context['active_exchanges'] = SkillExchangeSession.objects.filter(
            Q(exchange_request__sender=self.request.user) | Q(exchange_request__receiver=self.request.user),
            exchange_request__status='active'
        ).exclude(id=session.id).select_related('exchange_request__sender', 'exchange_request__receiver')
        
        return context

class SendExchangeMessageAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            content = data.get('content', '').strip()
            
            if not content:
                return JsonResponse({'status': 'error', 'message': 'Message cannot be empty'}, status=400)
                
            session = get_object_or_404(SkillExchangeSession, id=session_id)
            if request.user != session.exchange_request.sender and request.user != session.exchange_request.receiver:
                return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
                
            msg = SkillExchangeMessage.objects.create(
                session=session,
                sender=request.user,
                content=content
            )
            
            try:
                from notifications.utils import notify_exchange_message
                notify_exchange_message(request.user, session)
            except ImportError:
                pass
            
            return JsonResponse({
                'status': 'success', 
                'msg_id': msg.id,
                'sender': msg.sender.full_name or msg.sender.username,
                'content': msg.content,
                'timestamp': msg.timestamp.strftime('%H:%M')
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class GetExchangeMessagesAJAX(LoginRequiredMixin, View):
    def get(self, request, session_id, *args, **kwargs):
        session = get_object_or_404(SkillExchangeSession, id=session_id)
        if request.user != session.exchange_request.sender and request.user != session.exchange_request.receiver:
            return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
            
        last_id = request.GET.get('last_id')
        messages_qs = session.messages.all()
        
        if last_id:
            messages_qs = messages_qs.filter(id__gt=last_id)
            
        messages_list = []
        for m in messages_qs:
            messages_list.append({
                'id': m.id,
                'sender_id': m.sender.id,
                'sender_name': m.sender.full_name or m.sender.username,
                'content': m.content,
                'timestamp': m.timestamp.strftime('%H:%M'),
                'is_me': m.sender == request.user
            })
            
        # Mark as read
        session.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
            
        return JsonResponse({'status': 'success', 'messages': messages_list})
