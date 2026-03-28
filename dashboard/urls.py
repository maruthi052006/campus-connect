from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('stats/', views.DashboardStatsAJAX.as_view(), name='dashboard_stats'),
]
