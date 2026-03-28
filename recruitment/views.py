from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from .models import RecruitmentPost, RecruitmentApplication
from .forms import RecruitmentPostForm
from organizations.models import Organization, OrganizationMember
import json

class RecruitmentListView(LoginRequiredMixin, ListView):
    model = RecruitmentPost
    template_name = 'recruitment_list.html'
    context_object_name = 'posts'
    ordering = ['-created_at']
    
    def get_queryset(self):
        return super().get_queryset().select_related('organization').prefetch_related('required_skills')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['can_post_recruitment'] = (
            user.role in ['Teacher', 'Admin'] or 
            OrganizationMember.objects.filter(user=user, role='Admin').exists()
        )
        return context

class CreateRecruitmentPostView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = RecruitmentPost
    form_class = RecruitmentPostForm
    template_name = 'post_recruitment.html'
    success_url = reverse_lazy('recruitment:recruitment_list')
    
    def test_func(self):
        user = self.request.user
        if user.role in ['Teacher', 'Admin']:
            return True
        return OrganizationMember.objects.filter(user=user, role='Admin').exists()
        
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        if user.role in ['Teacher', 'Admin']:
            form.fields['organization'].queryset = Organization.objects.all()
        else:
            admin_org_ids = OrganizationMember.objects.filter(user=user, role='Admin').values_list('organization_id', flat=True)
            form.fields['organization'].queryset = Organization.objects.filter(id__in=admin_org_ids)
        return form

    def form_valid(self, form):
        post = form.save(commit=False)
        post.posted_by = self.request.user
        user = self.request.user
        
        # If user is Teacher/Admin, they can post for any org.
        # Otherwise, must be Admin of the specific org.
        if user.role not in ['Teacher', 'Admin']:
            if not OrganizationMember.objects.filter(user=user, role='Admin', organization=post.organization).exists():
                return self.form_invalid(form)
            
        post.save()
        form.save_m2m()
        return redirect('recruitment:recruitment_list')

class ApplyRecruitmentAJAX(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            post = get_object_or_404(RecruitmentPost, pk=pk)
            application, created = RecruitmentApplication.objects.get_or_create(post=post, applicant=request.user)
            if created:
                try:
                    from notifications.models import Notification
                    admins = OrganizationMember.objects.filter(organization=post.organization, role='Admin')
                    for admin in admins:
                        Notification.objects.create(
                            recipient=admin.user,
                            notif_type='org_join',
                            related_org=post.organization,
                            message=f"{request.user.full_name} applied for {post.title} at {post.organization.name}."
                        )
                except ImportError:
                    pass
                return JsonResponse({'status': 'success', 'message': 'Application submitted successfully.'})
            else:
                return JsonResponse({'status': 'info', 'message': 'You have already applied.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class OrganizationApplicationsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'applications_list.html'
    context_object_name = 'applications'
    
    def test_func(self):
        user = self.request.user
        if user.role in ['Teacher', 'Admin']:
            return True
        org_slug = self.kwargs.get('slug')
        org = get_object_or_404(Organization, slug=org_slug)
        return OrganizationMember.objects.filter(user=user, role='Admin', organization=org).exists()
        
    def get_queryset(self):
        user = self.request.user
        org = get_object_or_404(Organization, slug=self.kwargs.get('slug'))
        qs = RecruitmentApplication.objects.filter(post__organization=org).select_related('post', 'applicant')
        
        # If not a site-wide Teacher/Admin, only show posts created by the user or within their org
        if user.role not in ['Teacher', 'Admin']:
            qs = qs.filter(post__organization__members__user=user, post__organization__members__role='Admin')
            
        return qs.distinct()
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = get_object_or_404(Organization, slug=self.kwargs.get('slug'))
        return context

class UpdateApplicationStatusAJAX(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            if new_status not in ['accepted', 'rejected']:
                return JsonResponse({'status': 'error', 'message': 'Invalid status'}, status=400)
                
            application = get_object_or_404(RecruitmentApplication, pk=pk)
            post = application.post
            
            # Permission check: Teacher/Admin or Org Admin
            user = request.user
            is_authorized = (
                user.role in ['Teacher', 'Admin'] or
                OrganizationMember.objects.filter(user=user, role='Admin', organization=post.organization).exists()
            )
            
            if not is_authorized:
                return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
                
            application.status = new_status
            application.save()
            
            # Notify applicant
            try:
                from notifications.models import Notification
                Notification.objects.create(
                    recipient=application.applicant,
                    notif_type='org_join', # Reusing org_join type for simplicity or define new
                    message=f"Your application for {post.title} at {post.organization.name} has been {new_status}."
                )
            except ImportError:
                pass
                
            return JsonResponse({'status': 'success', 'message': f'Application {new_status} successfully.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class MyApplicationsListView(LoginRequiredMixin, ListView):
    template_name = 'my_applications.html'
    context_object_name = 'applications'
    
    def get_queryset(self):
        return RecruitmentApplication.objects.filter(applicant=self.request.user).select_related('post', 'post__organization')
