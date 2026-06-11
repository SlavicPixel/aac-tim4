from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, DeleteView

from users.mixins import CounselorRequiredMixin
from core.forms import DocumentForm
from core.models import Student, Document, AuditLog
from core.services import _log_action

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
        _log_action(self.request, AuditLog.CREATED, self.object)
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

        _log_action(self.request, AuditLog.DELETED, self.object)

        # Delete file from filesystem
        self.object.file.delete(save=False)
        self.object.delete()

        messages.success(self.request, f'Dokument "{document_name}" je obrisan.')
        return redirect('core:student_detail', pk=student_pk)