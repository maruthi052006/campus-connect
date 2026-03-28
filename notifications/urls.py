from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationsView.as_view(), name='notifications'),
    path('mark-read/', views.MarkReadAJAX.as_view(), name='mark_read_ajax'),
    path('mark-all-read/', views.MarkAllReadAJAX.as_view(), name='mark_all_read_ajax'),
    path('unread-count/', views.UnreadCountAJAX.as_view(), name='unread_count_ajax'),
]
