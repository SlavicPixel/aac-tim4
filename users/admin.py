from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Counselor, PeerSupportUser


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass


@admin.register(Counselor)
class CounselorAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']


@admin.register(PeerSupportUser)
class PeerSupportUserAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'student']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    list_filter = ['student']