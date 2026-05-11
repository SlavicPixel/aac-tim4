from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


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