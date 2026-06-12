from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('students/', views.StudentListView.as_view(), name='student_list'),
    path('students/new/', views.StudentCreateView.as_view(), name='student_create'),
    path('students/<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    path('students/<int:pk>/edit/', views.StudentUpdateView.as_view(), name='student_update'),
    path('students/<int:pk>/delete/', views.StudentDeleteView.as_view(), name='student_delete'),
    path('students/<int:pk>/reactivate/', views.student_reactivate, name='student_reactivate'),

    path('students/<int:student_pk>/documents/upload/', views.DocumentUploadView.as_view(), name='document_upload'),
    path('documents/<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='document_delete'),

    path('meetings/', views.MeetingListView.as_view(), name='meeting_list'),
    path('meetings/new/', views.MeetingCreateView.as_view(), name='meeting_create'),
    path('meetings/calendar/', views.MeetingCalendarView.as_view(), name='meeting_calendar'),
    path('meetings/<int:pk>/', views.MeetingDetailView.as_view(), name='meeting_detail'),
    path('meetings/<int:pk>/edit/', views.MeetingUpdateView.as_view(), name='meeting_update'),
    path('meetings/<int:pk>/delete/', views.MeetingDeleteView.as_view(), name='meeting_delete'),
    path('meetings/<int:pk>/reactivate/', views.meeting_reactivate, name='meeting_reactivate'),
    path('students/<int:student_pk>/meetings/new/', views.MeetingCreateView.as_view(), name='meeting_create_for_student'),

    path('students/<int:student_pk>/accommodations/new/', views.AccommodationCreateView.as_view(), name='accommodation_create'),
    path('accommodations/<int:pk>/', views.AccommodationDetailView.as_view(), name='accommodation_detail'),
    path('accommodations/<int:pk>/edit/', views.AccommodationUpdateView.as_view(), name='accommodation_update'),
    path('accommodations/<int:pk>/delete/', views.AccommodationDeleteView.as_view(), name='accommodation_delete'),
    path('accommodations/<int:pk>/pdf/', views.AccommodationPDFView.as_view(), name='accommodation_pdf'),

    path('peer-support-sessions/', views.PeerSupportSessionListView.as_view(), name='peer_support_session_list'),
    path('peer-support-sessions/new/', views.PeerSupportSessionCreateView.as_view(), name='peer_support_session_create'),
    path('peer-support-sessions/<int:pk>/', views.PeerSupportSessionDetailView.as_view(), name='peer_support_session_detail'),
    path('peer-support-sessions/<int:pk>/edit/', views.PeerSupportSessionUpdateView.as_view(), name='peer_support_session_update'),
    path('peer-support-sessions/<int:pk>/delete/', views.PeerSupportSessionDeleteView.as_view(), name='peer_support_session_delete'),
    path('peer-support-report/', views.PeerSupportMonthlyReportView.as_view(), name='peer_support_monthly_report'),
    path('peer-support-report/pdf/', views.PeerSupportMonthlyReportPDFView.as_view(), name='peer_support_monthly_report_pdf'),

    path('annual-report/', views.AnnualReportView.as_view(), name='annual_report'),
    path('annual-report/pdf/', views.AnnualReportPDFView.as_view(), name='annual_report_pdf'),
    path('annual-report/excel/', views.AnnualReportExcelView.as_view(), name='annual_report_excel'),

    path('students/<int:pk>/report/', views.StudentReportPDFView.as_view(), name='student_report_pdf'),

    path('api/guidelines/', views.guidelines_api, name='guidelines_api')
]