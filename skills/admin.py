from django.contrib import admin
from .models import SkillExchangeRequest, SkillExchangeSession

@admin.register(SkillExchangeRequest)
class SkillExchangeRequestAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'status', 'created_at')
    list_filter = ('status', 'created_at')

@admin.register(SkillExchangeSession)
class SkillExchangeSessionAdmin(admin.ModelAdmin):
    list_display = ('exchange_request', 'started_at', 'completed_at')
