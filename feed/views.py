import json
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Q
from .models import Post, Like, Comment, SavedPost
from .forms import CreatePostForm, CommentForm

class HomeView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'home.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        qs = Post.objects.select_related('author', 'author__profile').prefetch_related('likes').order_by('-is_pinned', '-created_at')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['form'] = CreatePostForm()
        context['comment_form'] = CommentForm()
        
        # Add liked and saved post IDs for the current user
        posts = context.get('posts', [])
        if user.is_authenticated:
            context['liked_post_ids'] = list(Like.objects.filter(user=user, post__in=posts).values_list('post_id', flat=True))
            context['saved_post_ids'] = list(SavedPost.objects.filter(user=user, post__in=posts).values_list('post_id', flat=True))
            
            # Increment impressions
            from django.db.models import F
            Post.objects.filter(id__in=[p.id for p in posts]).update(impressions=F('impressions') + 1)
        else:
            context['liked_post_ids'] = []
            context['saved_post_ids'] = []
            
        return context

from django.template.loader import render_to_string

class CreatePostView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = CreatePostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            
            try:
                from notifications.utils import notify_new_post
                notify_new_post(post)
            except ImportError:
                pass

            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('accept') == 'application/json':
                html = render_to_string('includes/post_card.html', {'post': post, 'user': request.user}, request=request)
                return JsonResponse({'status': 'success', 'post_id': post.id, 'html': html})
            return redirect('feed:home')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('accept') == 'application/json':
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
        return redirect('feed:home')

class DeletePostView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        post = get_object_or_404(Post, pk=pk, author=request.user)
        post.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('accept') == 'application/json':
            return JsonResponse({'status': 'success'})
        return redirect('feed:home')

class LikePostAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            post_id = data.get('post_id')
            post = get_object_or_404(Post, id=post_id)
            like, created = Like.objects.get_or_create(user=request.user, post=post)
            
            if not created:
                like.delete()
                liked = False
            else:
                liked = True
                try:
                    from notifications.utils import notify_like
                    notify_like(request.user, post)
                except ImportError:
                    pass
                
            count = post.likes.count()
            return JsonResponse({'status': 'success', 'liked': liked, 'count': count})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class CommentPostAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            post_id = data.get('post_id')
            content = data.get('content')
            parent_id = data.get('parent_id')
            
            post = get_object_or_404(Post, id=post_id)
            
            parent = None
            if parent_id:
                parent = get_object_or_404(Comment, id=parent_id)
                
            comment = Comment.objects.create(user=request.user, post=post, content=content, parent=parent)
            
            try:
                from notifications.utils import notify_comment
                notify_comment(request.user, post)
            except ImportError:
                pass
            
            html = render_to_string('partials/comment_item.html', {'comment': comment})
            return JsonResponse({'status': 'success', 'html': html})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class SavePostAJAX(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            post_id = data.get('post_id')
            post = get_object_or_404(Post, id=post_id)
            saved_post, created = SavedPost.objects.get_or_create(user=request.user, post=post)
            
            if not created:
                saved_post.delete()
                saved = False
            else:
                saved = True
                
            return JsonResponse({'saved': saved})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class SavedPostsView(LoginRequiredMixin, ListView):
    template_name = 'saved.html'
    context_object_name = 'saved_posts'
    paginate_by = 10
    
    def get_queryset(self):
        return SavedPost.objects.filter(user=self.request.user).select_related('post', 'post__author').order_by('-saved_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        saved_items = context.get('saved_posts', [])
        posts = [item.post for item in saved_items]
        
        if user.is_authenticated:
            context['liked_post_ids'] = list(Like.objects.filter(user=user, post__in=posts).values_list('post_id', flat=True))
            context['saved_post_ids'] = list(SavedPost.objects.filter(user=user, post__in=posts).values_list('post_id', flat=True))
        else:
            context['liked_post_ids'] = []
            context['saved_post_ids'] = []
            
        return context

class LoadMorePostsAJAX(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        page = request.GET.get('page', 1)
        # Infinite scroll logic goes here, currently a stub
        return JsonResponse({'html': '', 'has_next': False})
