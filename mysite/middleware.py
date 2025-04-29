from django.shortcuts import redirect
from django.contrib import messages

class BlockAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.is_staff:
            if request.path.startswith('/admin/'):
                return self.get_response(request)
            
            messages.warning(request, "Admin users are not allowed to access the main website.")
            return redirect('admin:index')
        
        return self.get_response(request) 