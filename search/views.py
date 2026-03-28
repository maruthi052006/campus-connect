from django.shortcuts import render
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from accounts.models import Skill, Profile

User = get_user_model()

class ExploreView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'explore.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        # Initial queryset: exclude self, select related profile and prefetch skills
        qs = User.objects.exclude(id=self.request.user.id).select_related('profile').prefetch_related('user_skills__skill')
        
        q = self.request.GET.get('q', '')
        skills = self.request.GET.getlist('skills[]') or self.request.GET.getlist('skills')
        domain = self.request.GET.getlist('domain[]') or self.request.GET.getlist('domain')
        department = self.request.GET.getlist('department[]') or self.request.GET.getlist('department')
        role = self.request.GET.get('role', '')
        batch = self.request.GET.get('batch', '')

        # Filter by search query
        if q:
            qs = qs.filter(
                Q(full_name__icontains=q) | 
                Q(username__icontains=q) | 
                Q(profile__domain__icontains=q)
            )
        
        # Filter by skills
        if skills:
            qs = qs.filter(user_skills__skill__name__in=skills)
            
        # Filter by domain
        if domain:
            qs = qs.filter(profile__domain__in=domain)
            
        # Filter by department
        if department:
            qs = qs.filter(department__in=department)
            
        # Filter by role
        if role and role != 'all':
            qs = qs.filter(role=role)
            
        # Filter by batch
        if batch and batch != 'all':
            qs = qs.filter(batch=batch)
                
        return qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch unique filter options
        context['all_skills'] = Skill.objects.all().order_by('name')
        context['all_domains'] = Profile.objects.exclude(domain='').values_list('domain', flat=True).distinct().order_by('domain')
        context['all_depts'] = User.objects.exclude(department='').values_list('department', flat=True).distinct().order_by('department')
        context['all_batches'] = User.objects.exclude(batch='').values_list('batch', flat=True).distinct().order_by('batch')
        
        # Check status for each user
        if self.request.user.is_authenticated:
            user = self.request.user
            from connections.models import Follow, Connection, ConnectionRequest
            
            # Following
            context['following_ids'] = list(Follow.objects.filter(follower=user).values_list('following_id', flat=True))
            
            # Connections
            conn_ids = set()
            conns = Connection.objects.filter(Q(user1=user) | Q(user2=user))
            for c in conns:
                conn_ids.add(c.user1_id)
                conn_ids.add(c.user2_id)
            context['connection_ids'] = list(conn_ids)
            
            # Pending Sent
            context['pending_sent_ids'] = list(ConnectionRequest.objects.filter(sender=user, status='pending').values_list('receiver_id', flat=True))
            
            # Pending Received
            context['pending_received_ids'] = list(ConnectionRequest.objects.filter(receiver=user, status='pending').values_list('sender_id', flat=True))
                
        return context

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax'):
            qs = self.get_queryset()
            paginator = Paginator(qs, self.paginate_by)
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
            
            # Check follow/connection state for AJAX
            following_ids = []
            connection_ids = []
            pending_sent_ids = []
            pending_received_ids = []
            try:
                from connections.models import Follow, Connection, ConnectionRequest
                user = self.request.user
                following_ids = list(Follow.objects.filter(follower=user).values_list('following_id', flat=True))
                
                conns = Connection.objects.filter(Q(user1=user) | Q(user2=user))
                conn_ids = set()
                for c in conns:
                    conn_ids.add(c.user1_id)
                    conn_ids.add(c.user2_id)
                connection_ids = list(conn_ids)
                
                pending_sent_ids = list(ConnectionRequest.objects.filter(sender=user, status='pending').values_list('receiver_id', flat=True))
                pending_received_ids = list(ConnectionRequest.objects.filter(receiver=user, status='pending').values_list('sender_id', flat=True))
            except ImportError:
                pass

            html = render_to_string('includes/user_cards.html', {
                'users': page_obj,
                'following_ids': following_ids,
                'connection_ids': connection_ids,
                'pending_sent_ids': pending_sent_ids,
                'pending_received_ids': pending_received_ids,
                'request': request
            })
            
            return JsonResponse({
                'html': html, 
                'count': qs.count(),
                'has_next': page_obj.has_next()
            })
            
        return super().get(request, *args, **kwargs)
