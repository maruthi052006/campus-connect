from django.urls import path
from . import views

app_name = 'recruitment'

urlpatterns = [
    path('', views.RecruitmentListView.as_view(), name='recruitment_list'),
    path('new/', views.CreateRecruitmentPostView.as_view(), name='create_recruitment'),
    path('<int:pk>/apply/', views.ApplyRecruitmentAJAX.as_view(), name='apply_recruitment_ajax'),
    path('my-applications/', views.MyApplicationsListView.as_view(), name='my_applications'),
    path('application/<int:pk>/status/', views.UpdateApplicationStatusAJAX.as_view(), name='update_application_status'),
    path('org/<slug:slug>/applications/', views.OrganizationApplicationsListView.as_view(), name='org_applications'),
]
