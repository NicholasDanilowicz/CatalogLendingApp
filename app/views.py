from django.shortcuts import render, redirect, get_object_or_404

from django.core.paginator import Paginator
from .forms import SearchForm
from .models import UserProfile
from .models import Equipment
from .models import Collection


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

def collection_detail(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    if not collection.can_user_access(request.user):
        return redirect('home')
    
    equipment_items = collection.equipment_items.all()
    print(f"Collection: {collection.title}")
    print(f"Equipment items count: {equipment_items.count()}")
    print(f"Equipment items: {[item.name for item in equipment_items]}")
    
    return render(request, 'collection_detail.html', {
        'collection': collection,
        'equipment_items': equipment_items
    })

def search_results(req):
    form = SearchForm(req.GET)
    query = req.GET.get('q', '')
    collection_id = req.GET.get('collection_id')
    tag = req.GET.get('tag')
    
    base_queryset = Equipment.objects.all()

    if collection_id:
        try:
            collection = Collection.objects.get(id=collection_id)
            base_queryset = base_queryset.filter(collections=collection)
        except Collection.DoesNotExist:
            pass
    elif tag:
        collections = Collection.objects.filter(tags__contains=tag, is_public=True)
        base_queryset = base_queryset.filter(collections__in=collections).distinct()

    if query:
        base_queryset = base_queryset.filter(name__icontains=query)

    paginator = Paginator(base_queryset, 5)
    page_number = req.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form, 
        'query': query,
        'page_obj': page_obj,
        'collection_id': collection_id,
        'tag': tag
    }
    
    return render(req, 'search_results.html', context)