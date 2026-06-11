from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import CreateView, ListView

from weasyprint import HTML

from users.mixins import PeerSupportRequiredMixin
from core.forms import PeerSupportSessionForm
from core.models import PeerSupportSession


class PeerSupportSessionCreateView(PeerSupportRequiredMixin, CreateView):
    model = PeerSupportSession
    form_class = PeerSupportSessionForm
    template_name = 'core/meeting_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['peer_support'] = self.request.user.peer_support_profile
        return kwargs

    def form_valid(self, form):
        form.instance.peer_support_user = self.request.user.peer_support_profile
        response = super().form_valid(form)
        messages.success(self.request, f'Sesija sa studentom {self.object.student.full_name} je uspješno evidentirana.')
        return response

    def get_success_url(self):
        return reverse('core:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Evidencija nove sesije vršnjačke podrške'
        context['submit_label'] = 'Evidentiraj sesiju'
        context['cancel_url'] = reverse('core:dashboard')
        return context
    
class PeerSupportSessionListView(PeerSupportRequiredMixin, ListView):
    model = PeerSupportSession
    template_name = 'core/peer_support_session_list.html'
    context_object_name = 'sessions'
    paginate_by = 20

    def get_queryset(self):
        queryset = PeerSupportSession.objects.filter(
            peer_support_user=self.request.user.peer_support_profile
        ).select_related('student')

        month = self.request.GET.get('month', '').strip()
        if month:
            try:
                year_str, month_str = month.split('-')
                queryset = queryset.filter(
                    date__year=int(year_str),
                    date__month=int(month_str)
                )
            except (ValueError, IndexError):
                pass

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_month'] = self.request.GET.get('month', '')

        total_minutes = sum(s.duration_minutes for s in self.get_queryset())
        context['total_hours'] = round(total_minutes / 60, 1)
        return context
    
class PeerSupportMonthlyReportView(PeerSupportRequiredMixin, ListView):
    model = PeerSupportSession
    template_name = 'core/peer_support_monthly_report.html'
    context_object_name = 'sessions'

    def _get_period(self):
        """Vraća (year, month) iz GET parametra 'period' (YYYY-MM), ili tekući mjesec."""
        period = self.request.GET.get('period', '').strip()
        today = timezone.now().date()
        if period:
            try:
                year_str, month_str = period.split('-')
                return int(year_str), int(month_str)
            except (ValueError, IndexError):
                pass
        return today.year, today.month

    def get_queryset(self):
        year, month = self._get_period()
        return PeerSupportSession.objects.filter(
            peer_support_user=self.request.user.peer_support_profile,
            date__year=year,
            date__month=month,
            date__lt=timezone.now().date(),
        ).select_related('student').order_by('date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year, month = self._get_period()
        sessions = self.get_queryset()

        total_minutes = sum(s.duration_minutes for s in sessions)

        # razrada po studentima
        per_student = {}
        for s in sessions:
            per_student.setdefault(s.student, 0)
            per_student[s.student] += s.duration_minutes
        per_student_list = [
            {'student': student, 'hours': round(minutes / 60, 1), 'minutes': minutes}
            for student, minutes in per_student.items()
        ]

        context['period'] = f"{year}-{month:02d}"
        context['year'] = year
        context['month'] = month
        context['total_hours'] = round(total_minutes / 60, 1)
        context['session_count'] = len(sessions)
        context['per_student'] = per_student_list
        return context


class PeerSupportMonthlyReportPDFView(PeerSupportRequiredMixin, ListView):
    model = PeerSupportSession

    def get(self, request, *args, **kwargs):
        period = request.GET.get('period', '').strip()
        today = timezone.now().date()
        try:
            year_str, month_str = period.split('-')
            year, month = int(year_str), int(month_str)
        except (ValueError, IndexError):
            year, month = today.year, today.month

        peer_support = request.user.peer_support_profile
        sessions = PeerSupportSession.objects.filter(
            peer_support_user=peer_support,
            date__year=year,
            date__month=month,
            date__lt=today,
        ).select_related('student').order_by('date')

        total_minutes = sum(s.duration_minutes for s in sessions)

        per_student = {}
        for s in sessions:
            per_student.setdefault(s.student, 0)
            per_student[s.student] += s.duration_minutes
        per_student_list = [
            {'student': student, 'hours': round(minutes / 60, 1)}
            for student, minutes in per_student.items()
        ]

        context = {
            'peer_support': peer_support,
            'sessions': sessions,
            'year': year,
            'month': month,
            'total_hours': round(total_minutes / 60, 1),
            'session_count': len(sessions),
            'per_student': per_student_list,
            'today': today,
        }

        html_string = render_to_string('core/peer_support_monthly_report_pdf.html', context)
        pdf = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"izvjestaj_{peer_support.user.last_name}_{year}_{month:02d}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response