from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView as AuthLoginView, LogoutView as AuthLogoutView, PasswordChangeView as AuthPasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, UpdateView, DetailView, View
from django.http import JsonResponse
import json
from django.db import models
from .models import User, Profile, Skill, UserSkill
from .forms import CustomLoginForm, ForcePasswordChangeForm, ProfileSetupForm, EditProfileForm, SkillForm
from feed.models import Post, Like, SavedPost

class CustomLoginView(AuthLoginView):
    form_class = CustomLoginForm
    template_name = 'login.html'

    def get_success_url(self):
        user = self.request.user
        if user.is_first_login:
            return reverse('accounts:force_password_change')
        if not user.is_profile_setup:
            return reverse('accounts:profile_setup')
        return self.request.GET.get('next', reverse('feed:home'))

class CustomLogoutView(AuthLogoutView):
    next_page = 'accounts:login'

class ForcePasswordChangeView(LoginRequiredMixin, AuthPasswordChangeView):
    template_name = 'first_login.html'
    form_class = ForcePasswordChangeForm
    success_url = reverse_lazy('accounts:profile_setup')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.is_first_login = False
        self.request.user.save()
        update_session_auth_hash(self.request, self.request.user)
        messages.success(self.request, "Password changed successfully. Please setup your profile.")
        return response

class ChangePasswordView(LoginRequiredMixin, AuthPasswordChangeView):
    template_name = 'settings.html'
    success_url = reverse_lazy('accounts:settings')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Password updated successfully.")
        return response

class ProfileSetupView(LoginRequiredMixin, UpdateView):
    template_name = 'profile_setup.html'
    form_class = ProfileSetupForm
    success_url = reverse_lazy('feed:home')

    def get_object(self):
        return self.request.user.profile

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        user.is_profile_setup = True
        
        role = self.request.POST.get('role')
        if role:
            user.role = role
        user.save()

        skills_data = self.request.POST.get('skills_data')
        if skills_data:
            try:
                skills_list = json.loads(skills_data)
                for skill_name in skills_list:
                    skill_name = skill_name.strip()
                    if skill_name:
                        skill, _ = Skill.objects.get_or_create(name__iexact=skill_name, defaults={'name': skill_name})
                        UserSkill.objects.get_or_create(user=user, skill=skill)
            except json.JSONDecodeError:
                pass
                
        messages.success(self.request, "Profile setup complete!")
        return super().form_valid(form)

class MyProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['profile_user'] = user
        context['profile'] = user.profile
        context['skills'] = user.user_skills.select_related('skill').all()
        
        context['posts'] = user.posts.all().order_by('-created_at')
        context['liked_post_ids'] = list(Like.objects.filter(user=user, post__in=context['posts']).values_list('post_id', flat=True))
        context['saved_post_ids'] = list(SavedPost.objects.filter(user=user, post__in=context['posts']).values_list('post_id', flat=True))
        context['projects'] = user.projects.all().order_by('-created_at')
        context['organizations'] = user.organization_memberships.select_related('organization').all()
        
        context['followers_count'] = user.followers.count()
        context['following_count'] = user.following.count()
        
        from connections.models import Connection
        from django.db.models import Q, Sum
        from django.utils import timezone
        from datetime import timedelta
        from dashboard.models import ProfileViewTracker

        context['connections_count'] = Connection.objects.filter(Q(user1=user) | Q(user2=user)).count()
        
        # Analytics
        seven_days_ago = timezone.now() - timedelta(days=7)
        context['profile_views'] = ProfileViewTracker.objects.filter(user=user, viewed_at__gte=seven_days_ago).count()
        context['post_impressions'] = user.posts.aggregate(total=Sum('impressions'))['total'] or 0
        
        return context

class EditProfileView(LoginRequiredMixin, UpdateView):
    template_name = 'edit_profile.html'
    form_class = EditProfileForm
    success_url = reverse_lazy('accounts:my_profile')

    def get_object(self):
        return self.request.user.profile

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        skills_data = self.request.POST.get('skills_data')
        if skills_data is not None:
            try:
                skills_list = json.loads(skills_data)
                user = self.request.user
                UserSkill.objects.filter(user=user).delete()
                for skill_name in skills_list:
                    skill_name = skill_name.strip()
                    if skill_name:
                        skill, _ = Skill.objects.get_or_create(name__iexact=skill_name, defaults={'name': skill_name})
                        UserSkill.objects.get_or_create(user=user, skill=skill)
            except json.JSONDecodeError:
                pass
                
        messages.success(self.request, "Profile updated successfully.")
        return super().form_valid(form)

class UserProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'user_profile.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.username == kwargs.get('username'):
            return redirect('accounts:my_profile')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target_user = self.object
        request_user = self.request.user
        context['profile'] = target_user.profile
        context['skills'] = target_user.user_skills.select_related('skill').all()
        context['posts'] = target_user.posts.all().order_by('-created_at')
        context['liked_post_ids'] = list(Like.objects.filter(user=request_user, post__in=context['posts']).values_list('post_id', flat=True))
        context['saved_post_ids'] = list(SavedPost.objects.filter(user=request_user, post__in=context['posts']).values_list('post_id', flat=True))
        context['projects'] = target_user.projects.all().order_by('-created_at')
        context['organizations'] = target_user.organization_memberships.select_related('organization').all()
        context['followers_count'] = target_user.followers.count()
        context['following_count'] = target_user.following.count()
        
        from connections.models import Connection, Follow, ConnectionRequest
        from django.db.models import Q
        
        context['connections_count'] = Connection.objects.filter(Q(user1=target_user) | Q(user2=target_user)).count()
        
        if request_user.is_authenticated and request_user != target_user:
            from dashboard.models import ProfileViewTracker
            ProfileViewTracker.objects.create(user=target_user, viewer=request_user)
            
            # Increment impressions for all their posts when visiting profile
            target_user.posts.update(impressions=models.F('impressions') + 1)
                
            context['is_following'] = Follow.objects.filter(follower=request_user, following=target_user).exists()
            
            is_connected = Connection.objects.filter(
                (Q(user1=request_user) & Q(user2=target_user)) | 
                (Q(user1=target_user) & Q(user2=request_user))
            ).exists()
            
            if is_connected:
                context['connection_status'] = 'connected'
            else:
                sent_req = ConnectionRequest.objects.filter(sender=request_user, receiver=target_user, status='pending').first()
                if sent_req:
                    context['connection_status'] = 'pending_sent'
                    context['pending_request_id'] = sent_req.id
                else:
                    received_req = ConnectionRequest.objects.filter(sender=target_user, receiver=request_user, status='pending').first()
                    if received_req:
                        context['connection_status'] = 'pending_received'
                        context['pending_request_id'] = received_req.id
                    else:
                        context['connection_status'] = 'none'

            user_conns = set(c.get_other_user(target_user) for c in Connection.objects.filter(Q(user1=target_user) | Q(user2=target_user)))
            req_user_conns = set(c.get_other_user(request_user) for c in Connection.objects.filter(Q(user1=request_user) | Q(user2=request_user)))
            context['mutual_connections_count'] = len(user_conns.intersection(req_user_conns))
                
        return context

class SkillManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'skills.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_skills'] = self.request.user.user_skills.select_related('skill').all()
        context['all_skills'] = Skill.objects.all()
        return context

class AddSkillAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            skill_name = data.get('skill_name', '').strip()
            if not skill_name:
                return JsonResponse({'status': 'error', 'message': 'Skill name is required'}, status=400)
            
            skill, created = Skill.objects.get_or_create(name__iexact=skill_name, defaults={'name': skill_name})
            user_skill, assigned = UserSkill.objects.get_or_create(user=request.user, skill=skill)
            
            if assigned:
                return JsonResponse({'status': 'success', 'message': 'Skill added', 'skill_id': skill.id, 'skill_name': skill.name})
            else:
                return JsonResponse({'status': 'info', 'message': 'Skill already added'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

class RemoveSkillAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            skill_id = data.get('skill_id')
            if not skill_id:
                 return JsonResponse({'status': 'error', 'message': 'Skill ID is required'}, status=400)
                 
            UserSkill.objects.filter(user=request.user, skill_id=skill_id).delete()
            return JsonResponse({'status': 'success', 'message': 'Skill removed'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.request.user.profile
        return context

class UpdatePrivacyAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            profile = request.user.profile
            profile.is_private = data.get('is_private', profile.is_private)
            profile.show_email = data.get('show_email', profile.show_email)
            profile.allow_connection_requests = data.get('allow_conn', profile.allow_connection_requests)
            profile.save()
            return JsonResponse({'status': 'success', 'message': 'Privacy settings updated'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class UpdateNotificationsAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            profile = request.user.profile
            profile.notif_likes = data.get('likes', profile.notif_likes)
            profile.notif_comments = data.get('comments', profile.notif_comments)
            profile.notif_connections = data.get('connections', profile.notif_connections)
            profile.notif_messages = data.get('messages', profile.notif_messages)
            profile.notif_projects = data.get('projects', profile.notif_projects)
            profile.notif_events = data.get('events', profile.notif_events)
            profile.save()
            return JsonResponse({'status': 'success', 'message': 'Notification preferences updated'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class ChangePasswordAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            current_password = data.get('current_password')
            new_password = data.get('new_password')
            
            user = request.user
            if not user.check_password(current_password):
                return JsonResponse({'status': 'error', 'message': 'Incorrect current password'}, status=400)
            
            from django.contrib.auth.password_validation import validate_password
            from django.core.exceptions import ValidationError
            try:
                validate_password(new_password, user)
            except ValidationError as e:
                return JsonResponse({'status': 'error', 'message': ' '.join(e.messages)}, status=400)
                
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            return JsonResponse({'status': 'success', 'message': 'Password updated successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


from django.contrib.auth.mixins import UserPassesTestMixin

class AddUserView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.role in ['Admin', 'Management'] or self.request.user.is_superuser)

    def get(self, request, *args, **kwargs):
        return render(request, 'add_user.html')

    def post(self, request, *args, **kwargs):
        try:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST

            username = data.get('roll_number')
            full_name = data.get('full_name')
            email = data.get('email')
            role = data.get('role', 'Student')
            department = data.get('department')
            batch = data.get('batch', '')

            if not username or not full_name or not email:
                return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({'status': 'error', 'message': f'User with Roll Number {username} already exists'}, status=400)

            # Create User
            user = User.objects.create_user(
                username=username,
                email=email,
                password=username,
                full_name=full_name,
                role=role,
                department=department,
                batch=batch,
                is_first_login=True,
                is_profile_setup=False
            )
            
            # Profile check (signal should handle this, but let's be bulletproof)
            if not hasattr(user, 'profile'):
                Profile.objects.create(user=user)

            # Welcome Notification
            from notifications.models import Notification
            Notification.objects.create(
                recipient=user,
                notif_type='welcome',
                message="Welcome to CampusConnect! Use your Roll Number as your default password to login."
            )

            return JsonResponse({
                'status': 'success',
                'message': 'User created successfully',
                'credentials': {
                    'username': username,
                    'password': username,
                    'full_name': full_name
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class BulkUploadView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.role in ['Admin', 'Management'] or self.request.user.is_superuser)

    def get(self, request, *args, **kwargs):
        return render(request, 'bulk_upload.html')

    def post(self, request, *args, **kwargs):
        import csv
        import io
        
        file = request.FILES.get('csv_file')
        if not file:
            return JsonResponse({'status': 'error', 'message': 'No file uploaded'}, status=400)
        
        if not file.name.endswith('.csv'):
            return JsonResponse({'status': 'error', 'message': 'Please upload a valid CSV file'}, status=400)

        results = []
        try:
            decoded_file = file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            for row in reader:
                un = row.get('roll_number') or row.get('username')
                fn = row.get('full_name')
                em = row.get('email')
                dept = row.get('department', '')
                btch = row.get('batch', '')
                rl = row.get('role', 'Student')

                if not un or not fn or not em:
                    results.append({'username': un or 'Unknown', 'status': 'Error', 'message': 'Missing required fields'})
                    continue

                if User.objects.filter(username=un).exists():
                    results.append({'username': un, 'status': 'Error', 'message': 'User already exists'})
                    continue

                try:
                    user = User.objects.create_user(
                        username=un, email=em, password=un,
                        full_name=fn, role=rl, department=dept, batch=btch,
                        is_first_login=True
                    )
                    if not hasattr(user, 'profile'):
                        Profile.objects.create(user=user)
                    results.append({'username': un, 'status': 'Success', 'message': 'Created'})
                except Exception as e:
                    results.append({'username': un, 'status': 'Error', 'message': str(e)})

            return JsonResponse({
                'status': 'success',
                'results': results,
                'summary': {
                    'total': len(results),
                    'success': len([r for r in results if r['status'] == 'Success']),
                    'error': len([r for r in results if r['status'] == 'Error'])
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Processing failed: {str(e)}'}, status=400)

class DownloadSampleCSVView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.role in ['Admin', 'Management'] or self.request.user.is_superuser)

    def get(self, request, *args, **kwargs):
        from django.http import HttpResponse
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="campusconnect_bulk_template.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['roll_number', 'full_name', 'email', 'role', 'department', 'batch'])
        writer.writerow(['2024CS101', 'John Doe', 'john.doe@campus.edu', 'Student', 'Computer Science & Engineering', '2026'])
        writer.writerow(['FAC102', 'Jane Smith', 'jane.smith@campus.edu', 'Teacher', 'Electronics & Communication Engineering', ''])
        
        return response
