from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from users.mixins import CounselorRequiredMixin
from .forms import StudentForm
from .models import Student, StudentCounselor


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