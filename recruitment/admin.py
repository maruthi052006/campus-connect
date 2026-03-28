from django.contrib import admin
from .models import RecruitmentPost, RecruitmentApplication

@admin.register(RecruitmentPost)
class RecruitmentPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'deadline', 'created_at')
    list_filter = ('deadline', 'created_at')

@admin.register(RecruitmentApplication)
class RecruitmentApplicationAdmin(admin.ModelAdmin):
    list_display = ('post', 'applicant', 'applied_at')
