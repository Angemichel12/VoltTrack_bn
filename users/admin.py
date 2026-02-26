# users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import User


# ─── Custom Forms ─────────────────────────────────────────────────────────────

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'name', 'role', 'station')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])  # hashed ✅
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('email', 'name', 'role', 'station', 'is_active')


# ─── Admin Class ──────────────────────────────────────────────────────────────

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form    = CustomUserCreationForm
    form        = CustomUserChangeForm
    model       = User

    # List view
    list_display    = ('email', 'name', 'role', 'station', 'is_active', 'created_at')
    list_filter     = ('role', 'is_active', 'station')
    search_fields   = ('email', 'name')
    ordering        = ('-created_at',)
    list_per_page   = 25

    # Detail view - editing existing user
    fieldsets = (
        ('Credentials',   {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name',)}),
        ('Role & Station',{'fields': ('role', 'station')}),
        ('Permissions',   {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Timestamps',    {'fields': ('created_at',), 'classes': ('collapse',)}),
    )
    readonly_fields = ('created_at',)

    # Add user view - creating new user
    add_fieldsets = (
        ('Account', {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2'),
        }),
        ('Role & Station', {
            'classes': ('wide',),
            'fields': ('role', 'station'),
        }),
        ('Status', {
            'classes': ('wide',),
            'fields': ('is_active', 'is_staff'),
        }),
    )