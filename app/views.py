from django.shortcuts import render, redirect
from .models import UserProfile


def custom_login(request):
    return render(request, 'login.html')


def home(request):
    if not request.user.is_authenticated:
        return render(request, 'home.html')

    try:
        user_profile = request.user.userprofile
        if user_profile.role == 'patron':
            return render(request, 'home.html')
        else:
            return render(request, 'librarian_home.html')
    except UserProfile.DoesNotExist:
        return redirect('select_role')


def select_role(request):
    try:
        request.user.userprofile
        return redirect('home')
    except UserProfile.DoesNotExist:
        if request.method == 'POST':
            role = request.POST.get('role')
            if role in ['patron', 'librarian']:
                UserProfile.objects.create(user=request.user, role=role)
                return redirect('home')
        
        return render(request, 'select_role.html')
