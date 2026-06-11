from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

from core.models import Student, Meeting, Accommodation, PeerSupportSession

from datetime import timedelta

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

            # --- Upozorenja i notifikacije ---
            threshold_no_meeting = today - timedelta(days=30)
            expiry_limit = today + timedelta(days=30)
            upcoming_limit = today + timedelta(days=7)

            # 1. Studenti bez sastanka dulje od 30 dana (gleda zadnji ODRŽANI sastanak)
            students_without_meetings = []
            for student in my_students:
                last_meeting = Meeting.objects.filter(
                    student=student,
                    counselor=counselor,
                    is_active=True,
                    date_time__date__lt=today,
                ).order_by('-date_time').first()

                if last_meeting is None:
                    students_without_meetings.append({
                        'student': student,
                        'last_date': None,
                    })
                elif last_meeting.date_time.date() < threshold_no_meeting:
                    students_without_meetings.append({
                        'student': student,
                        'last_date': last_meeting.date_time.date(),
                    })

            # 2. Prilagodbe pri isteku (aktivne, end_date unutar 30 dana)
            expiring_accommodations = Accommodation.objects.filter(
                student__in=my_students,
                status=Accommodation.ACTIVE,
                end_date__isnull=False,
                end_date__gte=today,
                end_date__lte=expiry_limit,
            ).select_related('student').order_by('end_date')

            # 3. Nadolazeći sastanci (idućih 7 dana)
            upcoming_meetings = Meeting.objects.filter(
                counselor=counselor,
                is_active=True,
                date_time__date__gte=today,
                date_time__date__lte=upcoming_limit,
            ).select_related('student').order_by('date_time')

            return render(request, 'core/dashboards/counselor_dashboard.html', {
                'counselor': counselor,
                'active_students_count': my_students.count(),
                'meetings_this_month': meetings_this_month,
                'active_accommodations_count': active_accommodations,
                'peer_support_hours': round(peer_minutes / 60, 1),
                'students_without_meetings': students_without_meetings,
                'expiring_accommodations': expiring_accommodations,
                'upcoming_meetings': upcoming_meetings,
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