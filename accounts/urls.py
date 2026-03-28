from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('change-password/', views.ForcePasswordChangeView.as_view(), name='force_password_change'),
    path('setup-profile/', views.ProfileSetupView.as_view(), name='profile_setup'),
    path('profile/', views.MyProfileView.as_view(), name='my_profile'),
    path('profile/edit/', views.EditProfileView.as_view(), name='edit_profile'),
    path('profile/<str:username>/', views.UserProfileView.as_view(), name='user_profile'),
    path('skills/', views.SkillManagementView.as_view(), name='skills'),
    path('skills/add/', views.AddSkillAJAX.as_view(), name='add_skill_ajax'),
    path('skills/remove/', views.RemoveSkillAJAX.as_view(), name='remove_skill_ajax'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('settings/update-privacy/', views.UpdatePrivacyAJAX.as_view(), name='update_privacy_ajax'),
    path('settings/update-notifications/', views.UpdateNotificationsAJAX.as_view(), name='update_notifications_ajax'),
    path('settings/change-password-ajax/', views.ChangePasswordAJAX.as_view(), name='change_password_ajax'),
    path('settings/password/', views.ChangePasswordView.as_view(), name='change_password'),
]
