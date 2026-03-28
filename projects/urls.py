from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='projects'),
    path('create/', views.CreateProjectAJAX.as_view(), name='create_project_ajax'),
    path('<int:pk>/edit/', views.EditProjectAJAX.as_view(), name='edit_project_ajax'),
    path('<int:pk>/delete/', views.DeleteProjectAJAX.as_view(), name='delete_project_ajax'),
    path('collaboration/', views.CollaborationView.as_view(), name='collaboration'),
    path('invite/respond/', views.HandleInviteAJAX.as_view(), name='handle_invite_ajax'),
]
