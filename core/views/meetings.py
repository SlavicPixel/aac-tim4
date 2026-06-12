from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView

from calendar import Calendar

from users.mixins import CounselorRequiredMixin
from core.forms import MeetingForm
from core.models import Student, Meeting

class MeetingCreateView(CounselorRequiredMixin, CreateView):
    model = Meeting
    form_class = MeetingForm
    template_name = 'core/meeting_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.student = None
        student_pk = kwargs.get('student_pk')
        if student_pk and hasattr(request.user, 'counselor_profile'):
            self.student = get_object_or_404(
                Student,
                pk=student_pk,
                counselors=request.user.counselor_profile
            )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['counselor'] = self.request.user.counselor_profile
        if self.student:
            kwargs['student'] = self.student
        return kwargs

    def form_valid(self, form):
        form.instance.counselor = self.request.user.counselor_profile
        # If student was locked in form, explicitly set it
        if self.student:
            form.instance.student = self.student
        response = super().form_valid(form)
        messages.success(self.request, f'Sastanak sa studentom {self.object.student.full_name} je uspješno evidentiran.')
        return response

    def get_success_url(self):
        return reverse('core:student_detail', kwargs={'pk': self.object.student.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Evidencija novog sastanka'
        context['submit_label'] = 'Evidentiraj sastanak'

        if self.student:
            context['cancel_url'] = reverse('core:student_detail', kwargs={'pk': self.student.pk})
        else:
            context['cancel_url'] = reverse('core:dashboard')

        return context
    
class MeetingListView(CounselorRequiredMixin, ListView):
    model = Meeting
    template_name = 'core/meeting_list.html'
    context_object_name = 'meetings'
    paginate_by = 20

    def get_queryset(self):
        queryset = Meeting.objects.filter(
            counselor=self.request.user.counselor_profile,
        ).select_related('student')

        status = self.request.GET.get('status', 'active').strip()
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'archived':
            queryset = queryset.filter(is_active=False)

        student_id = self.request.GET.get('student', '').strip()
        meeting_type = self.request.GET.get('type', '').strip()
        meeting_format = self.request.GET.get('format', '').strip()
        date_from = self.request.GET.get('date_from', '').strip()
        date_to = self.request.GET.get('date_to', '').strip()

        if student_id:
            queryset = queryset.filter(student_id=student_id)

        if meeting_type:
            queryset = queryset.filter(type=meeting_type)

        if meeting_format:
            queryset = queryset.filter(format=meeting_format)

        if date_from:
            try:
                from datetime import datetime
                parsed_date = datetime.strptime(date_from, '%d/%m/%Y')
                queryset = queryset.filter(date_time__date__gte=parsed_date.date())
            except ValueError:
                pass

        if date_to:
            try:
                from datetime import datetime
                parsed_date = datetime.strptime(date_to, '%d/%m/%Y')
                queryset = queryset.filter(date_time__date__lte=parsed_date.date())
            except ValueError:
                pass

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['students'] = Student.objects.filter(
            counselors=self.request.user.counselor_profile,
            is_active=True
        )
        context['type_choices'] = Meeting.TYPE_CHOICES
        context['format_choices'] = Meeting.FORMAT_CHOICES
        context['selected_student'] = self.request.GET.get('student', '')
        context['selected_type'] = self.request.GET.get('type', '')
        context['selected_format'] = self.request.GET.get('format', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['selected_status'] = self.request.GET.get('status', 'active')
        return context


class MeetingDetailView(CounselorRequiredMixin, DetailView):
    model = Meeting
    template_name = 'core/meeting_detail.html'
    context_object_name = 'meeting'

    def get_queryset(self):
        return Meeting.objects.filter(
            counselor=self.request.user.counselor_profile
        ).select_related('student', 'counselor__user')
    
class MeetingUpdateView(CounselorRequiredMixin, UpdateView):
    model = Meeting
    form_class = MeetingForm
    template_name = 'core/meeting_form.html'

    def get_queryset(self):
        return Meeting.objects.filter(
            counselor=self.request.user.counselor_profile
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['counselor'] = self.request.user.counselor_profile
        return kwargs

    def get_success_url(self):
        return reverse('core:meeting_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Uređivanje sastanka'
        context['submit_label'] = 'Spremi promjene'
        context['cancel_url'] = reverse('core:meeting_detail', kwargs={'pk': self.object.pk})
        return context


class MeetingDeleteView(CounselorRequiredMixin, DeleteView):
    model = Meeting
    template_name = 'core/meeting_confirm_delete.html'

    def get_queryset(self):
        return Meeting.objects.filter(
            counselor=self.request.user.counselor_profile
        )

    def get_success_url(self):
        return reverse('core:meeting_list')

    def form_valid(self, form):
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save()
        messages.success(self.request, 'Sastanak je arhiviran.')
        return redirect(self.get_success_url())


@login_required
def meeting_reactivate(request, pk):
    if not hasattr(request.user, 'counselor_profile'):
        return redirect('core:dashboard')

    meeting = get_object_or_404(
        Meeting,
        pk=pk,
        counselor=request.user.counselor_profile
    )
    meeting.is_active = True
    meeting.save()
    messages.success(request, 'Sastanak je reaktiviran.')
    return redirect('core:meeting_detail', pk=meeting.pk)

class MeetingCalendarView(CounselorRequiredMixin, ListView):
    template_name = 'core/meeting_calendar.html'
    context_object_name = 'meetings'

    def get_queryset(self):
        year, month = self._get_year_month()
        return Meeting.objects.filter(
            counselor=self.request.user.counselor_profile,
            is_active=True,
            date_time__year=year,
            date_time__month=month
        ).select_related('student').order_by('date_time')

    def _get_year_month(self):
        today = timezone.now().date()
        try:
            year = int(self.request.GET.get('year', today.year))
            month = int(self.request.GET.get('month', today.month))
            if month < 1 or month > 12:
                raise ValueError
        except (ValueError, TypeError):
            year, month = today.year, today.month
        return year, month

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year, month = self._get_year_month()
        today = timezone.now().date()

        # Group meetings by day
        meetings_by_day = {}
        for meeting in context['meetings']:
            day = meeting.date_time.day
            meetings_by_day.setdefault(day, []).append(meeting)

        # Generate calendar grid (weeks of (day, is_current_month) tuples)
        cal = Calendar(firstweekday=0)  # Monday = 0
        weeks = []
        for week in cal.monthdatescalendar(year, month):
            week_data = []
            for day_date in week:
                is_current_month = day_date.month == month
                day_meetings = meetings_by_day.get(day_date.day, []) if is_current_month else []
                week_data.append({
                    'date': day_date,
                    'is_current_month': is_current_month,
                    'is_today': day_date == today,
                    'meetings': day_meetings,
                })
            weeks.append(week_data)

        # Navigation
        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1

        if month == 12:
            next_year, next_month = year + 1, 1
        else:
            next_year, next_month = year, month + 1

        croatian_months = [
            'Siječanj', 'Veljača', 'Ožujak', 'Travanj', 'Svibanj', 'Lipanj',
            'Srpanj', 'Kolovoz', 'Rujan', 'Listopad', 'Studeni', 'Prosinac'
        ]

        context.update({
            'year': year,
            'month': month,
            'month_name': croatian_months[month - 1],
            'weeks': weeks,
            'prev_year': prev_year,
            'prev_month': prev_month,
            'next_year': next_year,
            'next_month': next_month,
            'today_year': today.year,
            'today_month': today.month,
            'weekday_names': ['Pon', 'Uto', 'Sri', 'Čet', 'Pet', 'Sub', 'Ned'],
        })

        return context