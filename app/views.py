from django.shortcuts import render, redirect, get_object_or_404

from django.core.paginator import Paginator
from .forms import SearchForm
from .models import UserProfile
from .models import Equipment


def custom_login(request):
    return render(request, 'login.html')


def home(request):
    if not request.user.is_authenticated:
        return render(request, 'home.html')

    try:
        user_profile = request.user.userprofile
        form = SearchForm()
        if request.method == 'GET':
            form = SearchForm(request.GET)
            if form.is_valid():
                query = form.cleaned_data["query"]
        if user_profile.role == 'patron':
            return render(request, 'home.html', {"form": form})
        else:
            return render(request, 'librarian_home.html', {"form": form})
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=request.user, role='patron')
        return render(request, 'home.html', {"form": SearchForm()})

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

def item_detail(request, item_id):
    item = get_object_or_404(Equipment, id=item_id)
    return render(request, 'item_detail.html', {'item': item})

def search_results(req):
    form = SearchForm(req.GET)
    query = req.GET.get('q', '')
    print("here is query: ", query)
    results = []
    if form.is_valid():
        query = form.cleaned_data.get('query', '')
        print("cleaned query: ", query)
        if query:
            results = Equipment.objects.filter(name__icontains=query)
    paginator = Paginator(results, 5)
    page_number = req.GET.get('page')
    page_obj = paginator.get_page(page_number)
    print("whatever page_obj is: ", page_obj)
    return render(req, 'search_results.html', {'form': form, 'query': query, 'results': results, 'page_obj': page_obj})