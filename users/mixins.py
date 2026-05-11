from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect


class CounselorRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        if not hasattr(request.user, 'counselor_profile'):
            return redirect('core:dashboard')

        return super().dispatch(request, *args, **kwargs)