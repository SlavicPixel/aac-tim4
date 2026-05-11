from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('students/new/', views.StudentCreateView.as_view(), name='student_create'),
]