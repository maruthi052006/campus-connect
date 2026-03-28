from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import json
from .models import Notification

class NotificationsView(LoginRequiredMixin, TemplateView):
    template_name = 'notifications.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        
        all_notifs = Notification.objects.filter(recipient=user).order_by('-created_at')
        
        context['today'] = all_notifs.filter(created_at__gte=today_start)
        context['week'] = all_notifs.filter(created_at__gte=week_start, created_at__lt=today_start)
        context['earlier'] = all_notifs.filter(created_at__lt=week_start)
        
        return context

class MarkReadAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            notif_id = data.get('notif_id')
            notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
            notif.is_read = True
            notif.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class MarkAllReadAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})

class UnreadCountAJAX(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        unread_qs = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
        count = unread_qs.count()
        latest = unread_qs.first()
        
        data = {
            'status': 'success',
            'count': count,
        }
        if latest:
            data['latest_msg'] = latest.message
            data['latest_url'] = latest.get_url()
            
        return JsonResponse(data)
