from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView

from users.mixins import CounselorRequiredMixin
from .forms import StudentForm, DocumentForm
from .models import Student, StudentCounselor, Document


@login_required
def dashboard(request):
    user = request.user

    if hasattr(user, 'counselor_profile'):
        return render(request, 'core/dashboards/counselor_dashboard.html', {
            'counselor': user.counselor_profile,
        })
    elif hasattr(user, 'peer_support_profile'):
        return render(request, 'core/dashboards/peer_support_dashboard.html', {
            'peer_support': user.peer_support_profile,
        })
    else:
        return redirect('admin:index')


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
        return context
    
class StudentDetailView(CounselorRequiredMixin, DetailView):
    model = Student
    template_name = 'core/student_detail.html'
    context_object_name = 'student'

    def get_queryset(self):
        return Student.objects.filter(
            counselors=self.request.user.counselor_profile
        )


class StudentUpdateView(CounselorRequiredMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'core/student_form.html'

    def get_queryset(self):
        return Student.objects.filter(
            counselors=self.request.user.counselor_profile
        )

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
    messages.success(request, f'Student {student.full_name} je reaktiviran.')
    return redirect('core:student_detail', pk=student.pk)

class DocumentUploadView(CounselorRequiredMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = 'core/document_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.student = get_object_or_404(
            Student,
            pk=kwargs['student_pk'],
            counselors=request.user.counselor_profile if hasattr(request.user, 'counselor_profile') else None
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.student = self.student
        form.instance.file_type = form.cleaned_data['file'].name.split('.')[-1].lower()
        response = super().form_valid(form)
        messages.success(self.request, f'Dokument "{self.object.name}" je uspješno uploadan.')
        return response

    def get_success_url(self):
        return reverse('core:student_detail', kwargs={'pk': self.student.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = self.student
        context['form_title'] = f'Upload dokumenta za studenta: {self.student.full_name}'
        context['submit_label'] = 'Uploadaj dokument'
        context['cancel_url'] = reverse('core:student_detail', kwargs={'pk': self.student.pk})
        return context


class DocumentDeleteView(CounselorRequiredMixin, DeleteView):
    model = Document
    template_name = 'core/document_confirm_delete.html'

    def get_queryset(self):
        return Document.objects.filter(
            student__counselors=self.request.user.counselor_profile
        )

    def get_success_url(self):
        return reverse('core:student_detail', kwargs={'pk': self.object.student.pk})

    def form_valid(self, form):
        self.object = self.get_object()
        student_pk = self.object.student.pk
        document_name = self.object.name
        
        # Delete file from filesystem
        self.object.file.delete(save=False)
        self.object.delete()
        
        messages.success(self.request, f'Dokument "{document_name}" je obrisan.')
        return redirect('core:student_detail', pk=student_pk)