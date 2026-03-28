from django.urls import path
from . import views

app_name = 'campus_events'

urlpatterns = [
    path('', views.EventListView.as_view(), name='event_list'),
    path('create/', views.EventCreateView.as_view(), name='event_create'),
    path('delete/<int:pk>/', views.EventDeleteView.as_view(), name='event_delete'),
    path('ajax/list/', views.EventsAJAX.as_view(), name='events_ajax'),
]
