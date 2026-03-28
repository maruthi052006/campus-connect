from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q
import json
from .models import Project, ProjectInvite, ProjectCollaborator
from .forms import ProjectForm
from accounts.models import Skill

class ProjectListView(LoginRequiredMixin, ListView):
    template_name = 'projects.html'
    context_object_name = 'projects'

    def get_queryset(self):
        # Start with all projects
        qs = Project.objects.all().order_by('-created_at').prefetch_related('tech_stack', 'owner')
        
        # Search
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
            
        # Skill filter
        skill_id = self.request.GET.get('skill')
        if skill_id:
            qs = qs.filter(tech_stack__id=skill_id)
            
        # "My Projects" filter
        mine = self.request.GET.get('mine')
        if mine == 'true':
            qs = qs.filter(owner=self.request.user)
            
        return qs.distinct()
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ProjectForm()
        # Only show skills that are actually used in projects
        context['skills'] = Skill.objects.filter(projects__isnull=False).distinct()
        return context

class CreateProjectAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            form.save_m2m() # important for many-to-many
            
            techs = ", ".join([skill.name for skill in project.tech_stack.all()])
            thumbnail_url = project.thumbnail.url if project.thumbnail else ""
            img_tag = f'<img src="{thumbnail_url}" class="card-img-top" alt="{project.title}" style="height: 180px; object-fit: cover;">' if thumbnail_url else ''
            
            html = f'''
            <div class="col-md-6 col-lg-4 mb-4" id="project-{project.id}">
                <div class="card h-100 shadow-sm project-card">
                    {img_tag}
                    <div class="card-body">
                        <h5 class="card-title">{project.title}</h5>
                        <p class="card-text text-muted small">{techs}</p>
                        <p class="card-text">{project.description[:100]}...</p>
                    </div>
                </div>
            </div>
            '''
            return JsonResponse({'status': 'success', 'html': html, 'project_id': project.id})
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

class EditProjectAJAX(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk, owner=request.user)
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            project = form.save()
            return JsonResponse({'status': 'success', 'message': 'Project updated'})
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

class DeleteProjectAJAX(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk, owner=request.user)
        project.delete()
        return JsonResponse({'status': 'success', 'message': 'Project deleted'})

class CollaborationView(LoginRequiredMixin, TemplateView):
    template_name = 'collaboration.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_invites'] = ProjectInvite.objects.filter(
            invitee=self.request.user, 
            status='pending'
        ).select_related('project', 'inviter')
        context['active_collaborations'] = ProjectCollaborator.objects.filter(
            user=self.request.user
        ).select_related('project', 'project__owner')
        return context

class HandleInviteAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            invite_id = data.get('invite_id')
            action = data.get('action') # 'accept' or 'decline'

            invite = get_object_or_404(ProjectInvite, id=invite_id, invitee=request.user, status='pending')

            if action == 'accept':
                invite.status = 'accepted'
                invite.save()
                
                # Add to collaborators
                ProjectCollaborator.objects.get_or_create(
                    project=invite.project,
                    user=request.user,
                    defaults={'role': invite.role_offered}
                )
                return JsonResponse({'status': 'success', 'message': f'You have joined {invite.project.title}'})
            
            elif action == 'decline':
                invite.status = 'declined'
                invite.save()
                return JsonResponse({'status': 'success', 'message': 'Invitation declined'})

            return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
