from django.urls import path
from . import views

app_name = 'skills'

urlpatterns = [
    path('exchange/', views.SkillExchangeDashboardView.as_view(), name='skill_exchange'),
    path('exchange/new/', views.NewExchangeRequestView.as_view(), name='new_exchange_request'),
    path('exchange/accept/', views.AcceptExchangeAJAX.as_view(), name='accept_exchange_ajax'),
    path('exchange/reject/', views.RejectExchangeAJAX.as_view(), name='reject_exchange_ajax'),
    path('exchange/withdraw/', views.WithdrawExchangeAJAX.as_view(), name='withdraw_exchange_ajax'),
    path('exchange/complete/', views.CompleteExchangeAJAX.as_view(), name='complete_exchange_ajax'),
    
    # Chat URLs
    path('exchange/chat/<int:session_id>/', views.SkillExchangeChatView.as_view(), name='exchange_chat'),
    path('exchange/chat/send/', views.SendExchangeMessageAJAX.as_view(), name='send_exchange_message_ajax'),
    path('exchange/chat/messages/<int:session_id>/', views.GetExchangeMessagesAJAX.as_view(), name='get_exchange_messages_ajax'),
]
