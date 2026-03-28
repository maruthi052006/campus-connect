from django.shortcuts import redirect
from django.urls import reverse

class LoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Exempt paths
            exempt_names = ['accounts:logout', 'accounts:force_password_change', 'accounts:profile_setup']
            exempt_paths = [reverse(name) for name in exempt_names if name]
            
            if request.path not in exempt_paths and not request.path.startswith('/admin/') and not request.path.startswith('/static/') and not request.path.startswith('/media/'):
                if getattr(request.user, 'is_first_login', False):
                    return redirect('accounts:force_password_change')
                elif not getattr(request.user, 'is_profile_setup', False):
                    return redirect('accounts:profile_setup')

        response = self.get_response(request)
        return response
