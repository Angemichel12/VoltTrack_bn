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
        fields = ('phone_number', 'name', 'role')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])  # hashed ✅
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('phone_number', 'name', 'role', 'is_active')


# ─── Admin Class ──────────────────────────────────────────────────────────────

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form    = CustomUserCreationForm
    form        = CustomUserChangeForm
    model       = User

    # List view
    list_display    = ('phone_number', 'name', 'role', 'is_active', 'created_at')
    list_filter     = ('role', 'is_active')
    search_fields   = ('phone_number', 'name')
    ordering        = ('-created_at',)
    list_per_page   = 25

    # Detail view - editing existing user
    fieldsets = (
        ('Credentials',   {'fields': ('phone_number', 'password')}),
        ('Personal Info', {'fields': ('name',)}),
        ('Role',          {'fields': ('role',)}),
        ('Permissions',   {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Timestamps',    {'fields': ('created_at',), 'classes': ('collapse',)}),
    )
    readonly_fields = ('created_at',)

    # Add user view - creating new user
    add_fieldsets = (
        ('Account', {
            'classes': ('wide',),
            'fields': ('phone_number', 'name', 'password1', 'password2'),
        }),
        ('Role', {
            'classes': ('wide',),
            'fields': ('role',),
        }),
        ('Status', {
            'classes': ('wide',),
            'fields': ('is_active', 'is_staff'),
        }),
    )