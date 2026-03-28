import json
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, View, TemplateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.utils import timezone
from .models import Organization, OrganizationMember, JoinRequest, RecruitmentPost, RecruitmentApplication
from .forms import OrganizationForm
from feed.models import Post, Like, SavedPost


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        org_slug = self.kwargs.get('slug')
        org = get_object_or_404(Organization, slug=org_slug)
        return OrganizationMember.objects.filter(
            organization=org, user=self.request.user, role='Admin'
        ).exists()


class OrganizationListView(LoginRequiredMixin, ListView):
    model = Organization
    template_name = 'organizations.html'
    context_object_name = 'organizations'
    ordering = ['-created_at']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # Organizations the user is a member of
        context['my_orgs'] = OrganizationMember.objects.filter(
            user=user
        ).select_related('organization')
        # Slugs of orgs where user has a pending join request
        context['pending_slugs'] = list(
            JoinRequest.objects.filter(user=user, status='pending')
            .values_list('organization__slug', flat=True)
        )
        # Slugs of orgs where user is already a member
        context['member_slugs'] = list(
            OrganizationMember.objects.filter(user=user)
            .values_list('organization__slug', flat=True)
        )
        return context


class CreateOrganizationView(LoginRequiredMixin, CreateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'create_org.html'
    success_url = reverse_lazy('organizations:organizations')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['org_types'] = Organization.ORG_TYPES
        return context

    def form_valid(self, form):
        org = form.save(commit=False)
        org.created_by = self.request.user
        org.save()
        OrganizationMember.objects.create(organization=org, user=self.request.user, role='Admin')
        return redirect('organizations:org_profile', slug=org.slug)


class OrganizationProfileView(LoginRequiredMixin, DetailView):
    model = Organization
    template_name = 'org_profile.html'
    context_object_name = 'organization'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.object
        user = self.request.user
        membership = OrganizationMember.objects.filter(organization=org, user=user).first()
        context['is_member'] = membership is not None
        context['is_admin'] = membership is not None and membership.role == 'Admin'
        context['is_moderator'] = membership is not None and membership.role in ('Admin', 'Moderator')
        context['join_request'] = JoinRequest.objects.filter(organization=org, user=user, status='pending').first()
        context['member_count'] = org.members.count()
        context['org_members'] = org.members.select_related('user__profile').all()
        context['org_posts'] = Post.objects.filter(organization=org).order_by('-is_pinned', '-created_at')[:10]
        context['liked_post_ids'] = list(Like.objects.filter(user=user, post__in=context['org_posts']).values_list('post_id', flat=True))
        context['saved_post_ids'] = list(SavedPost.objects.filter(user=user, post__in=context['org_posts']).values_list('post_id', flat=True))
        context['admins'] = org.members.filter(role='Admin').select_related('user')
        from connections.models import Follow
        context['following_ids'] = list(Follow.objects.filter(follower=user).values_list('following_id', flat=True))
        return context


from django.views.generic import ListView, DetailView, CreateView, UpdateView, View, TemplateView

class OrganizationDashboardView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = Organization
    template_name = 'org_dashboard.html'
    context_object_name = 'organization'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.object
        context['member_count'] = org.members.count()
        context['pending_count'] = JoinRequest.objects.filter(organization=org, status='pending').count()
        # For template consistency
        context['pending_requests'] = context['pending_count']
        context['post_count'] = Post.objects.filter(organization=org, post_type='organization').count()
        context['recruitment_count'] = RecruitmentPost.objects.filter(organization=org).count()
        context['recent_members'] = org.members.select_related('user').order_by('-joined_at')[:5]
        return context

class UpdateOrganizationView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'edit_org.html'
    
    def get_success_url(self):
        return reverse('organizations:org_profile', kwargs={'slug': self.object.slug})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = self.object
        return context


class OrganizationMembersView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    template_name = 'members.html'
    context_object_name = 'members'

    def get_queryset(self):
        org = get_object_or_404(Organization, slug=self.kwargs.get('slug'))
        return OrganizationMember.objects.filter(organization=org).select_related('user', 'user__profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = get_object_or_404(Organization, slug=self.kwargs.get('slug'))
        return context


class OrganizationJoinRequestsView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    template_name = 'join_requests.html'
    context_object_name = 'join_requests'

    def get_queryset(self):
        org = get_object_or_404(Organization, slug=self.kwargs.get('slug'))
        return JoinRequest.objects.filter(organization=org, status='pending').select_related('user', 'user__profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = get_object_or_404(Organization, slug=self.kwargs.get('slug'))
        return context


class OrganizationPostsView(LoginRequiredMixin, DetailView):
    model = Organization
    template_name = 'org_posts.html'
    context_object_name = 'organization'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.object
        user = self.request.user
        membership = OrganizationMember.objects.filter(organization=org, user=user).first()
        context['is_admin'] = membership is not None and membership.role == 'Admin'
        context['is_moderator'] = membership is not None and membership.role in ('Admin', 'Moderator')
        post_type = self.request.GET.get('type', 'all')
        posts_qs = Post.objects.filter(organization=org).order_by('-is_pinned', '-created_at')
        if post_type in ('announcement', 'event', 'recruitment'):
            posts_qs = posts_qs.filter(category__iexact=post_type)
        context['org_posts'] = posts_qs
        context['liked_post_ids'] = list(Like.objects.filter(user=user, post__in=posts_qs).values_list('post_id', flat=True))
        context['saved_post_ids'] = list(SavedPost.objects.filter(user=user, post__in=posts_qs).values_list('post_id', flat=True))
        context['post_type'] = post_type
        return context


class OrganizationRecruitmentView(LoginRequiredMixin, DetailView):
    model = Organization
    template_name = 'recruitment.html'
    context_object_name = 'organization'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.object
        user = self.request.user
        membership = OrganizationMember.objects.filter(organization=org, user=user).first()
        context['is_admin'] = membership is not None and membership.role == 'Admin'
        context['is_moderator'] = membership is not None and membership.role in ('Admin', 'Moderator')
        recruitment_posts = RecruitmentPost.objects.filter(organization=org).order_by('-created_at')
        context['recruitment_posts'] = recruitment_posts
        context['applied_ids'] = list(
            RecruitmentApplication.objects.filter(
                user=user, post__in=recruitment_posts
            ).values_list('post_id', flat=True)
        )
        return context


# ─── AJAX VIEWS ──────────────────────────────────────────────────────────────

class JoinToggleAJAX(LoginRequiredMixin, View):
    def post(self, request, slug, *args, **kwargs):
        try:
            body = request.body.decode('utf-8') if request.body else '{}'
            data = json.loads(body) if body else {}
            org = get_object_or_404(Organization, slug=slug)
            message = data.get('message', '')

            member = OrganizationMember.objects.filter(organization=org, user=request.user).first()
            if member:
                member.delete()
                return JsonResponse({'status': 'success', 'state': 'left'})

            req = JoinRequest.objects.filter(organization=org, user=request.user, status='pending').first()
            if req:
                req.delete()
                return JsonResponse({'status': 'success', 'state': 'withdrawn'})

            JoinRequest.objects.create(organization=org, user=request.user, message=message)

            try:
                from notifications.utils import notify_org_join
                notify_org_join(request.user, org)
            except (ImportError, Exception):
                pass

            return JsonResponse({'status': 'success', 'state': 'requested'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


class AcceptJoinAJAX(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, slug, *args, **kwargs):
        try:
            body = request.body.decode('utf-8') if request.body else '{}'
            data = json.loads(body)
            req_id = data.get('request_id')
            org = get_object_or_404(Organization, slug=slug)
            join_req = get_object_or_404(JoinRequest, id=req_id, organization=org, status='pending')

            join_req.status = 'accepted'
            join_req.save()

            OrganizationMember.objects.get_or_create(organization=org, user=join_req.user)

            try:
                from notifications.utils import notify_org_accept
                notify_org_accept(join_req.user, org)
            except (ImportError, Exception):
                pass

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


class RejectJoinAJAX(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, slug, *args, **kwargs):
        try:
            body = request.body.decode('utf-8') if request.body else '{}'
            data = json.loads(body)
            req_id = data.get('request_id')
            org = get_object_or_404(Organization, slug=slug)
            join_req = get_object_or_404(JoinRequest, id=req_id, organization=org, status='pending')

            join_req.status = 'rejected'
            join_req.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


class UpdateMemberRoleAJAX(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, slug, *args, **kwargs):
        try:
            data = json.loads(request.body)
            member_id = data.get('member_id')
            new_role = data.get('role')
            valid_roles = [r[0] for r in OrganizationMember.ROLE_CHOICES]
            if new_role not in valid_roles:
                return JsonResponse({'status': 'error', 'message': 'Invalid role'}, status=400)
            org = get_object_or_404(Organization, slug=slug)
            member = get_object_or_404(OrganizationMember, id=member_id, organization=org)
            # Prevent demoting yourself if you are the only admin
            if member.user == request.user and new_role != 'Admin':
                admin_count = org.members.filter(role='Admin').count()
                if admin_count <= 1:
                    return JsonResponse({'status': 'error', 'message': 'Cannot demote the only admin'}, status=400)
            member.role = new_role
            member.save()
            return JsonResponse({'status': 'success', 'role': new_role})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


class RemoveMemberAJAX(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, slug, *args, **kwargs):
        try:
            data = json.loads(request.body)
            member_id = data.get('member_id')
            org = get_object_or_404(Organization, slug=slug)
            member = get_object_or_404(OrganizationMember, id=member_id, organization=org)
            # Cannot remove yourself
            if member.user == request.user:
                return JsonResponse({'status': 'error', 'message': 'Cannot remove yourself'}, status=400)
            member.delete()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


class CreateRecruitmentPostAJAX(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, slug, *args, **kwargs):
        try:
            data = json.loads(request.body)
            org = get_object_or_404(Organization, slug=slug)
            title = data.get('title', '').strip()
            description = data.get('description', '').strip()
            skills_required = data.get('skills_required', '')
            deadline_str = data.get('deadline')
            if not title or not description:
                return JsonResponse({'status': 'error', 'message': 'Title and description required'}, status=400)
            deadline = None
            if deadline_str:
                from datetime import date
                try:
                    deadline = date.fromisoformat(deadline_str)
                except ValueError:
                    pass
            post = RecruitmentPost.objects.create(
                organization=org,
                created_by=request.user,
                title=title,
                description=description,
                skills_required=skills_required,
                deadline=deadline
            )
            return JsonResponse({'status': 'success', 'id': post.id, 'title': post.title})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


class ApplyRecruitmentAJAX(LoginRequiredMixin, View):
    def post(self, request, slug, pk, *args, **kwargs):
        try:
            org = get_object_or_404(Organization, slug=slug)
            rec_post = get_object_or_404(RecruitmentPost, id=pk, organization=org)
            _, created = RecruitmentApplication.objects.get_or_create(
                post=rec_post, user=request.user
            )
            if not created:
                return JsonResponse({'status': 'error', 'message': 'Already applied'}, status=400)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class OrganizationCreatePostAJAX(LoginRequiredMixin, View):
    def post(self, request, slug, *args, **kwargs):
        try:
            org = get_object_or_404(Organization, slug=slug)
            # Check if user is admin or moderator
            membership = OrganizationMember.objects.filter(organization=org, user=request.user).first()
            if not membership or membership.role not in ('Admin', 'Moderator'):
                return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
            
            content = request.POST.get('content', '').strip()
            post_type = request.POST.get('category', 'announcement') # default to announcement
            image = request.FILES.get('image')
            
            if not content:
                return JsonResponse({'status': 'error', 'message': 'Content required'}, status=400)
            
            post = Post.objects.create(
                author=request.user,
                content=content,
                post_type='organization',
                category=post_type, # Using the value from request (Announcement, etc.)
                organization=org,
                image=image
            )
            return JsonResponse({'status': 'success', 'post_id': post.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


class OrganizationPinPostAJAX(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, slug, *args, **kwargs):
        try:
            data = json.loads(request.body)
            post_id = data.get('post_id')
            action = data.get('action') # 'pin' or 'unpin'
            
            org = get_object_or_404(Organization, slug=slug)
            post = get_object_or_404(Post, id=post_id, organization=org)
            
            # Toggle pinned status if no explicit action provided
            if action == 'pin':
                post.is_pinned = True
            elif action == 'unpin':
                post.is_pinned = False
            else:
                post.is_pinned = not post.is_pinned
            
            post.save()
            return JsonResponse({'status': 'success', 'pinned': post.is_pinned})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

