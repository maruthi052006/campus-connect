from django.urls import path
from . import views

app_name = 'organizations'

urlpatterns = [
    path('', views.OrganizationListView.as_view(), name='organizations'),
    path('create/', views.CreateOrganizationView.as_view(), name='create_org'),
    path('<slug:slug>/', views.OrganizationProfileView.as_view(), name='org_profile'),
    path('<slug:slug>/dashboard/', views.OrganizationDashboardView.as_view(), name='org_dashboard'),
    path('<slug:slug>/edit/', views.UpdateOrganizationView.as_view(), name='edit_org'),
    path('<slug:slug>/members/', views.OrganizationMembersView.as_view(), name='org_members'),
    path('<slug:slug>/requests/', views.OrganizationJoinRequestsView.as_view(), name='org_requests'),
    path('<slug:slug>/posts/', views.OrganizationPostsView.as_view(), name='org_posts'),
    path('<slug:slug>/recruitment/', views.OrganizationRecruitmentView.as_view(), name='org_recruitment'),

    # AJAX endpoints — join/leave
    path('<slug:slug>/join/', views.JoinToggleAJAX.as_view(), name='org_join_toggle'),
    # AJAX endpoints — join requests (accept/reject)
    path('<slug:slug>/requests/accept/', views.AcceptJoinAJAX.as_view(), name='org_accept_join'),
    path('<slug:slug>/requests/reject/', views.RejectJoinAJAX.as_view(), name='org_reject_join'),
    # AJAX endpoints — member management
    path('<slug:slug>/members/update-role/', views.UpdateMemberRoleAJAX.as_view(), name='org_update_role'),
    path('<slug:slug>/members/remove/', views.RemoveMemberAJAX.as_view(), name='org_remove_member'),
    # AJAX endpoints — recruitment
    path('<slug:slug>/recruitment/create/', views.CreateRecruitmentPostAJAX.as_view(), name='org_create_recruitment'),
    path('<slug:slug>/recruitment/<int:pk>/apply/', views.ApplyRecruitmentAJAX.as_view(), name='org_apply_recruitment'),
    # AJAX endpoints — posts
    path('<slug:slug>/posts/create/', views.OrganizationCreatePostAJAX.as_view(), name='org_create_post'),
    path('<slug:slug>/posts/pin/', views.OrganizationPinPostAJAX.as_view(), name='org_pin_post'),
]
