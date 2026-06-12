from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView

from users.mixins import CounselorRequiredMixin
from core.forms import StudentForm
from core.models import Student, StudentCounselor, PeerSupportSession, AuditLog
from core.services import _log_action

class StudentCreateView(CounselorRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'core/student_form.html'
    success_url = reverse_lazy('core:student_list')

    def form_valid(self, form):
            response = super().form_valid(form)
            StudentCounselor.objects.create(
                student=self.object,
                counselor=self.request.user.counselor_profile
            )
            _log_action(self.request, AuditLog.CREATED, self.object)
            return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Registracija novog studenta'
        context['submit_label'] = 'Registriraj studenta'
        context['cancel_url'] = reverse_lazy('core:student_list')
        return context
    
class StudentListView(CounselorRequiredMixin, ListView):
    model = Student
    template_name = 'core/student_list.html'
    context_object_name = 'students'
    paginate_by = 20

    def get_queryset(self):
        queryset = Student.objects.filter(
            counselors=self.request.user.counselor_profile
        )

        search = self.request.GET.get('search', '').strip()
        faculty = self.request.GET.get('faculty', '').strip()
        year = self.request.GET.get('year', '').strip()
        show_archived = self.request.GET.get('show_archived', '')

        # Defaultno samo aktivni; arhivirani se uključuju samo ako je checkbox označen
        if not show_archived:
            queryset = queryset.filter(is_active=True)

        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        if faculty:
            queryset = queryset.filter(faculty__icontains=faculty)

        if year:
            queryset = queryset.filter(year_of_study=year)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['faculty'] = self.request.GET.get('faculty', '')
        context['year'] = self.request.GET.get('year', '')
        context['show_archived'] = self.request.GET.get('show_archived', '')
        return context
    
class StudentDetailView(CounselorRequiredMixin, DetailView):
    model = Student
    template_name = 'core/student_detail.html'
    context_object_name = 'student'

    def get_queryset(self):
        return Student.objects.filter(
            counselors=self.request.user.counselor_profile
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object

        peer_support_data = []
        for peer in student.peer_supporters.all():
            sessions = PeerSupportSession.objects.filter(
                peer_support_user=peer,
                student=student,
                date__lt=timezone.now().date(),
            )
            total_minutes = sum(s.duration_minutes for s in sessions)
            peer_support_data.append({
                'peer': peer,
                'session_count': sessions.count(),
                'total_hours': round(total_minutes / 60, 1),
            })

        context['peer_support_data'] = peer_support_data
        return context


class StudentUpdateView(CounselorRequiredMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'core/student_form.html'

    def get_queryset(self):
        return Student.objects.filter(
            counselors=self.request.user.counselor_profile
        )
    
    def form_valid(self, form):
            response = super().form_valid(form)
            _log_action(self.request, AuditLog.UPDATED, self.object)
            return response

    def get_success_url(self):
        return reverse_lazy('core:student_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'Uređivanje studenta: {self.object.full_name}'
        context['submit_label'] = 'Spremi promjene'
        context['cancel_url'] = reverse('core:student_detail', kwargs={'pk': self.object.pk})
        return context


class StudentDeleteView(CounselorRequiredMixin, DeleteView):
    model = Student
    template_name = 'core/student_confirm_delete.html'
    success_url = reverse_lazy('core:student_list')

    def get_queryset(self):
        return Student.objects.filter(
            counselors=self.request.user.counselor_profile
        )

    def form_valid(self, form):
            self.object = self.get_object()
            self.object.is_active = False
            self.object.save()
            _log_action(self.request, AuditLog.UPDATED, self.object)
            messages.success(self.request, f'Student {self.object.full_name} je arhiviran.')
            return redirect(self.success_url)


@login_required
def student_reactivate(request, pk):
    if not hasattr(request.user, 'counselor_profile'):
        return redirect('core:dashboard')

    student = get_object_or_404(
        Student,
        pk=pk,
        counselors=request.user.counselor_profile
    )
    student.is_active = True
    student.save()
    _log_action(request, AuditLog.UPDATED, student)
    messages.success(request, f'Student {student.full_name} je reaktiviran.')
    return redirect('core:student_detail', pk=student.pk)