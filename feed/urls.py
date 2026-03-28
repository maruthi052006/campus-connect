from django.urls import path
from . import views

app_name = 'feed'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('post/create/', views.CreatePostView.as_view(), name='create_post'),
    path('post/<int:pk>/delete/', views.DeletePostView.as_view(), name='delete_post'),
    path('post/like/', views.LikePostAJAX.as_view(), name='like_post_ajax'),
    path('post/comment/', views.CommentPostAJAX.as_view(), name='comment_post_ajax'),
    path('post/save/', views.SavePostAJAX.as_view(), name='save_post_ajax'),
    path('saved/', views.SavedPostsView.as_view(), name='saved_posts'),
    path('load-more/', views.LoadMorePostsAJAX.as_view(), name='load_more_posts'),
]
