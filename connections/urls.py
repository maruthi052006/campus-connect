from django.urls import path
from . import views

app_name = 'connections'

urlpatterns = [
    path('', views.ConnectionsView.as_view(), name='connections'),
    path('requests/', views.RequestsView.as_view(), name='connection_requests'),
    path('follow/', views.FollowToggleAJAX.as_view(), name='follow_toggle_ajax'),
    path('request/send/', views.SendConnectionRequestAJAX.as_view(), name='send_connection_request_ajax'),
    path('request/accept/', views.AcceptRequestAJAX.as_view(), name='accept_request_ajax'),
    path('request/accept-user/', views.AcceptUserConnectionAJAX.as_view(), name='accept_user_ajax'),
    path('request/reject/', views.RejectRequestAJAX.as_view(), name='reject_request_ajax'),
    path('request/withdraw/', views.WithdrawRequestAJAX.as_view(), name='withdraw_request_ajax'),
    path('remove/', views.RemoveConnectionAJAX.as_view(), name='remove_connection_ajax'),
    path('suggestions/', views.SuggestedUsersAJAX.as_view(), name='suggestions_ajax'),
]
