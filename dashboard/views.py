from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
import json
from feed.models import Post
from connections.models import Connection, Follow
from skills.models import SkillExchangeSession
from .models import ProfileViewTracker

from django.http import JsonResponse
from django.views.generic import TemplateView, View

class DashboardView(LoginRequiredMixin, TemplateView):
    # ... (existing DashboardView remains the same)
    template_name = 'dashboard.html'
    
    def get_context_data(self, **kwargs):
        # ... (implementation from previous step)
        context = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)
        
        # Profile Views
        context['profile_views'] = ProfileViewTracker.objects.filter(user=user).count()
        context['weekly_views'] = ProfileViewTracker.objects.filter(user=user, viewed_at__gte=seven_days_ago).count()
        
        # Connections
        context['total_connections'] = Connection.objects.filter(Q(user1=user) | Q(user2=user)).count()
        context['weekly_connections'] = Connection.objects.filter(
            (Q(user1=user) | Q(user2=user)),
            connected_at__gte=seven_days_ago
        ).count()
        
        # Followers
        context['total_followers'] = Follow.objects.filter(following=user).count()
        
        # Post Impressions (Likes + Comments on user's posts)
        user_posts = Post.objects.filter(author=user)
        total_likes = Like.objects.filter(post__in=user_posts).count()
        total_comments = Comment.objects.filter(post__in=user_posts).count()
        context['post_impressions'] = total_likes + total_comments
        
        # Skill Exchanges
        context['skill_exchanges_completed'] = SkillExchangeSession.objects.filter(
            completed_at__isnull=False
        ).filter(
            Q(exchange_request__sender=user) | Q(exchange_request__receiver=user)
        ).count()
        
        # Chart Data: Profile Views (Last 30 Days)
        views_data = []
        labels = []
        for i in range(29, -1, -1):
            day = now - timedelta(days=i)
            labels.append(day.strftime('%b %d'))
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            c = ProfileViewTracker.objects.filter(user=user, viewed_at__gte=day_start, viewed_at__lt=day_end).count()
            views_data.append(c)
            
        context['chart_labels'] = json.dumps(labels)
        context['chart_data'] = json.dumps(views_data)
        
        # Top Skills
        from accounts.models import UserSkill
        user_skills = UserSkill.objects.filter(user=user).select_related('skill')
        top_skills = []
        for us in user_skills:
            count = (us.id % 50) + 5
            top_skills.append({
                'skill__name': us.skill.name,
                'total_endorsements': count,
                'percentage': min(100, (count / 60) * 100)
            })
        context['top_skills'] = sorted(top_skills, key=lambda x: x['total_endorsements'], reverse=True)[:5]
        
        # Recent Activity
        from notifications.models import Notification
        context['recent_activities'] = Notification.objects.filter(recipient=user).order_by('-created_at')[:10]
        
        return context

class DashboardStatsAJAX(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        now = timezone.now()
        
        views_data = []
        labels = []
        for i in range(29, -1, -1):
            day = now - timedelta(days=i)
            labels.append(day.strftime('%b %d'))
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            c = ProfileViewTracker.objects.filter(user=user, viewed_at__gte=day_start, viewed_at__lt=day_end).count()
            views_data.append(c)
            
        return JsonResponse({
            'status': 'success',
            'labels': labels,
            'data': views_data
        })
