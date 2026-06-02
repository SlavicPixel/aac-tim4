from django.contrib import admin
from .models import Disability, Student, StudentCounselor, Document, Accommodation, Meeting, Guideline, PeerSupportSession


@admin.register(Disability)
class DisabilityAdmin(admin.ModelAdmin):
    list_display = ['name', 'type']
    list_filter = ['type']
    search_fields = ['name']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'faculty', 'study_program', 'year_of_study']
    list_filter = ['faculty', 'year_of_study']
    search_fields = ['first_name', 'last_name']


@admin.register(StudentCounselor)
class StudentCounselorAdmin(admin.ModelAdmin):
    list_display = ['student', 'counselor', 'assigned_date']
    list_filter = ['assigned_date']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'student', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['name', 'student__first_name', 'student__last_name']


@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    list_display = ['student', 'type', 'status', 'start_date', 'end_date']
    list_filter = ['type', 'status']
    search_fields = ['description', 'student__first_name', 'student__last_name']

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['student', 'counselor', 'date_time', 'type', 'format', 'is_active']
    list_filter = ['type', 'format', 'is_active', 'date_time']
    search_fields = ['student__first_name', 'student__last_name', 'notes']
    date_hierarchy = 'date_time'

@admin.register(Guideline)
class GuidelineAdmin(admin.ModelAdmin):
    list_display = ['title']
    search_fields = ['title', 'content']
    filter_horizontal = ['disabilities']

@admin.register(PeerSupportSession)
class PeerSupportSessionAdmin(admin.ModelAdmin):
    list_display = ['peer_support_user', 'student', 'date', 'duration_minutes']
    list_filter = ['date']
    search_fields = [
        'peer_support_user__user__first_name',
        'peer_support_user__user__last_name',
        'student__first_name',
        'student__last_name',
    ]
    date_hierarchy = 'date'