from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Profile, Skill, UserSkill
from django import forms

class AddUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'full_name', 'role', 'department', 'batch')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password('campus123') # Default password
        if commit:
            user.save()
        return user

@admin.action(description="Bulk generate default passwords for selected users")
def reset_passwords(modeladmin, request, queryset):
    for user in queryset:
        user.set_password('campus123')
        user.is_first_login = True
        user.save()

class CustomUserAdmin(UserAdmin):
    add_form = AddUserForm
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('full_name', 'email')}),
        (_('Campus Info'), {'fields': ('role', 'department', 'batch', 'is_first_login', 'is_profile_setup')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'full_name', 'role', 'department', 'batch'),
        }),
    )
    list_display = ('username', 'full_name', 'role', 'department', 'is_staff')
    actions = [reset_passwords]

admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile)
admin.site.register(Skill)
admin.site.register(UserSkill)
