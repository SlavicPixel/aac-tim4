from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect


class CounselorRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        if not hasattr(request.user, 'counselor_profile'):
            return redirect('core:dashboard')

        return super().dispatch(request, *args, **kwargs)
    
class PeerSupportRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        if not hasattr(request.user, 'peer_support_profile'):
            return redirect('core:dashboard')

        return super().dispatch(request, *args, **kwargs)
    
class AdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        if not request.user.is_superuser:
            return redirect('core:dashboard')

        return super().dispatch(request, *args, **kwargs)