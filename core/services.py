from .models import AuditLog, Meeting, Student, PeerSupportSession, Disability, Accommodation
from users.models import Counselor

def _log_action(request, action, obj, model_name=None):
    """zapisuje izmjenu u AuditLogu"""
    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        model_name=model_name or obj.__class__.__name__,
        object_id=obj.pk,
        object_repr=str(obj)[:255],
    )

def _build_annual_report_data(year):
    """Agregira podatke godišnjeg izvještaja AAC-a za zadanu godinu."""

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