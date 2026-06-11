from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView

from weasyprint import HTML

from users.mixins import CounselorRequiredMixin
from core.forms import AccommodationForm
from core.models import Student, Accommodation, Disability, Guideline, AuditLog
from core.services import _log_action

class AccommodationCreateView(CounselorRequiredMixin, CreateView):
    model = Accommodation
    form_class = AccommodationForm
    template_name = 'core/accommodation_form.html'

    def dispatch(self, request, *args, **kwargs):
        if hasattr(request.user, 'counselor_profile'):
            self.student = get_object_or_404(
                Student,
                pk=kwargs['student_pk'],
                counselors=request.user.counselor_profile
            )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
            form.instance.student = self.student
            response = super().form_valid(form)
            _log_action(self.request, AuditLog.CREATED, self.object)
            messages.success(self.request, 'Prilagodba je uspješno kreirana.')
            return response

    def get_success_url(self):
        return reverse('core:student_detail', kwargs={'pk': self.student.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = self.student
        context['form_title'] = f'Nova prilagodba za studenta: {self.student.full_name}'
        context['submit_label'] = 'Kreiraj prilagodbu'
        context['cancel_url'] = reverse('core:student_detail', kwargs={'pk': self.student.pk})
        return context


class AccommodationDetailView(CounselorRequiredMixin, DetailView):
    model = Accommodation
    template_name = 'core/accommodation_detail.html'
    context_object_name = 'accommodation'

    def get_queryset(self):
        return Accommodation.objects.filter(
            student__counselors=self.request.user.counselor_profile
        ).select_related('student', 'disability')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.disability:
            context['guidelines'] = Guideline.objects.filter(
                disabilities=self.object.disability
            )
        else:
            context['guidelines'] = Guideline.objects.none()
        return context


class AccommodationUpdateView(CounselorRequiredMixin, UpdateView):
    model = Accommodation
    form_class = AccommodationForm
    template_name = 'core/accommodation_form.html'

    def get_queryset(self):
        return Accommodation.objects.filter(
            student__counselors=self.request.user.counselor_profile
        )
    
    def form_valid(self, form):
        response = super().form_valid(form)
        _log_action(self.request, AuditLog.UPDATED, self.object)
        return response

    def get_success_url(self):
        return reverse('core:accommodation_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = self.object.student
        context['form_title'] = f'Uređivanje prilagodbe za studenta: {self.object.student.full_name}'
        context['submit_label'] = 'Spremi promjene'
        context['cancel_url'] = reverse('core:accommodation_detail', kwargs={'pk': self.object.pk})
        return context


class AccommodationDeleteView(CounselorRequiredMixin, DeleteView):
    model = Accommodation
    template_name = 'core/accommodation_confirm_delete.html'

    def get_queryset(self):
        return Accommodation.objects.filter(
            student__counselors=self.request.user.counselor_profile
        )

    def get_success_url(self):
        return reverse('core:student_detail', kwargs={'pk': self.object.student.pk})

    def form_valid(self, form):
        self.object = self.get_object()
        student_pk = self.object.student.pk
        _log_action(self.request, AuditLog.DELETED, self.object)
        self.object.delete()
        messages.success(self.request, 'Prilagodba je obrisana.')
        return redirect('core:student_detail', pk=student_pk)
    
@login_required
def guidelines_api(request):
    """
    API endpoint that returns guidelines for a given disability.
    Used by the accommodation form to dynamically load guidelines.
    """
    if not hasattr(request.user, 'counselor_profile'):
        return JsonResponse({'guidelines': []}, status=403)
    
    disability_id = request.GET.get('disability')
    if not disability_id:
        return JsonResponse({'guidelines': []})

    try:
        disability = Disability.objects.get(pk=disability_id)
    except Disability.DoesNotExist:
        return JsonResponse({'guidelines': []})

    guidelines = Guideline.objects.filter(disabilities=disability)
    data = {
        'guidelines': [
            {'title': g.title, 'content': g.content}
            for g in guidelines
        ]
    }
    return JsonResponse(data)

class AccommodationPDFView(CounselorRequiredMixin, DetailView):
    """
    Generates a PDF document for an accommodation that can be sent to the coordinator.
    """
    model = Accommodation

    def get_queryset(self):
        return Accommodation.objects.filter(
            student__counselors=self.request.user.counselor_profile
        ).select_related('student', 'disability')

    def get(self, request, *args, **kwargs):
        accommodation = self.get_object()

        if accommodation.disability:
            guidelines = Guideline.objects.filter(disabilities=accommodation.disability)
        else:
            guidelines = Guideline.objects.none()

        context = {
            'accommodation': accommodation,
            'student': accommodation.student,
            'counselor': request.user.counselor_profile,
            'guidelines': guidelines,
            'today': timezone.now().date(),
        }

        html_string = render_to_string('core/accommodation_pdf.html', context)
        html = HTML(string=html_string)
        pdf = html.write_pdf()

        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"prilagodba_{accommodation.student.last_name}_{accommodation.pk}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'

        return response