from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView

from calendar import Calendar, month_name
from datetime import date, datetime
from weasyprint import HTML
import openpyxl

from users.mixins import CounselorRequiredMixin, PeerSupportRequiredMixin, AdminRequiredMixin
from .forms import StudentForm, DocumentForm, MeetingForm, AccommodationForm, PeerSupportSessionForm
from .models import Student, StudentCounselor, Document, Meeting, Accommodation, Disability, Guideline, PeerSupportSession

@login_required
def dashboard(request):
    user = request.user

    if hasattr(user, 'counselor_profile'):
            counselor = user.counselor_profile
            today = timezone.now().date()

            my_students = Student.objects.filter(counselors=counselor, is_active=True)

            meetings_this_month = Meeting.objects.filter(
                counselor=counselor,
                is_active=True,
                date_time__year=today.year,
                date_time__month=today.month,
            ).count()

            active_accommodations = Accommodation.objects.filter(
                student__in=my_students,
                status=Accommodation.ACTIVE,
            ).count()

            # sati vršnjačke podrške za studente ovog savjetnika (odradjene sesije)
            peer_sessions = PeerSupportSession.objects.filter(
                student__in=my_students,
                date__lt=today,
            )
            peer_minutes = sum(s.duration_minutes for s in peer_sessions)

            return render(request, 'core/dashboards/counselor_dashboard.html', {
                'counselor': counselor,
                'active_students_count': my_students.count(),
                'meetings_this_month': meetings_this_month,
                'active_accommodations_count': active_accommodations,
                'peer_support_hours': round(peer_minutes / 60, 1),
            })
    elif hasattr(user, 'peer_support_profile'):
            peer_support = user.peer_support_profile
            today = timezone.now().date()
            sessions = peer_support.sessions.select_related('student')

            upcoming_sessions = sessions.filter(date__gte=today).order_by('date')
            past_sessions = sessions.filter(date__lt=today).order_by('-date')

            total_minutes = sum(s.duration_minutes for s in past_sessions)

            # Suma minuta za tekući mjesec
            month_minutes = sum(
                s.duration_minutes for s in past_sessions
                if s.date.year == today.year and s.date.month == today.month
            )

            return render(request, 'core/dashboards/peer_support_dashboard.html', {
                'peer_support': peer_support,
                'students': peer_support.students.all(),
                'upcoming_sessions': upcoming_sessions,
                'past_sessions': past_sessions,
                'total_hours': round(total_minutes / 60, 1),
                'month_hours': round(month_minutes / 60, 1),
            })
    else:
            if user.is_superuser:
                return redirect('core:annual_report')
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
            is_active=True
        ).select_related('student')

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
        self.object.delete()
        messages.success(self.request, 'Prilagodba je obrisana.')
        return redirect('core:student_detail', pk=student_pk)
    
@login_required
def guidelines_api(request):
    """
    API endpoint that returns guidelines for a given disability.
    Used by the accommodation form to dynamically load guidelines.
    """
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
    
def _build_annual_report_data(year):
    """Agregira podatke godišnjeg izvještaja AAC-a za zadanu godinu."""
    from users.models import Counselor

    # po savjetniku: broj sastanaka i broj jedinstvenih studenata u toj godini
    per_counselor = []
    for counselor in Counselor.objects.all():
        meetings = Meeting.objects.filter(
            counselor=counselor,
            is_active=True,
            date_time__year=year,
        )
        student_ids = meetings.values_list('student_id', flat=True).distinct()
        per_counselor.append({
            'counselor': counselor,
            'meeting_count': meetings.count(),
            'student_count': len(set(student_ids)),
        })

    total_meetings = Meeting.objects.filter(
        is_active=True, date_time__year=year
    ).count()
    active_students = Student.objects.filter(is_active=True).count()

    peer_minutes = sum(
        s.duration_minutes for s in PeerSupportSession.objects.filter(date__year=year)
    )

    # broj jedinstvenih studenata po vrsti teškoce
    per_disability = []
    for disability in Disability.objects.all():
        student_ids = Accommodation.objects.filter(
            disability=disability,
            start_date__year=year,
        ).values_list('student_id', flat=True).distinct()
        count = len(set(student_ids))
        if count > 0:
            per_disability.append({
                'disability': disability,
                'count': count,
            })

    return {
        'year': year,
        'per_counselor': per_counselor,
        'total_meetings': total_meetings,
        'active_students': active_students,
        'peer_support_hours': round(peer_minutes / 60, 1),
        'per_disability': per_disability,
    }

class AnnualReportView(AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        year = self._get_year(request)
        data = _build_annual_report_data(year)
        data['available_years'] = self._available_years()
        return render(request, 'core/annual_report.html', data)

    def _get_year(self, request):
        year_param = request.GET.get('year', '').strip()
        if year_param.isdigit():
            return int(year_param)
        return timezone.now().year

    def _available_years(self):
        years = set()
        for m in Meeting.objects.all():
            years.add(m.date_time.year)
        years.add(timezone.now().year)
        return sorted(years, reverse=True)


class AnnualReportPDFView(AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        year_param = request.GET.get('year', '').strip()
        year = int(year_param) if year_param.isdigit() else timezone.now().year

        data = _build_annual_report_data(year)
        data['today'] = timezone.now().date()

        html_string = render_to_string('core/annual_report_pdf.html', data)
        pdf = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="godisnji_izvjestaj_{year}.pdf"'
        return response


class AnnualReportExcelView(AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        year_param = request.GET.get('year', '').strip()
        year = int(year_param) if year_param.isdigit() else timezone.now().year

        data = _build_annual_report_data(year)

        wb = openpyxl.Workbook()

        # List 1: Sažetak
        ws = wb.active
        ws.title = 'Sažetak'
        ws.append([f'Godišnji izvještaj AAC-a za {year}. godinu'])
        ws.append([])
        ws.append(['Aktivni studenti', data['active_students']])
        ws.append(['Ukupno sastanaka', data['total_meetings']])
        ws.append(['Sati vršnjačke podrške', data['peer_support_hours']])

        # List 2: Po savjetniku
        ws2 = wb.create_sheet('Po savjetniku')
        ws2.append(['Savjetnik', 'Broj sastanaka', 'Broj studenata'])
        for row in data['per_counselor']:
            ws2.append([row['counselor'].full_name, row['meeting_count'], row['student_count']])

        # List 3: Vrste teškoća
        ws3 = wb.create_sheet('Vrste teškoća')
        ws3.append(['Vrsta teškoće', 'Broj studenata'])
        for row in data['per_disability']:
            ws3.append([row['disability'].name, row['count']])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="godisnji_izvjestaj_{year}.xlsx"'
        wb.save(response)
        return response