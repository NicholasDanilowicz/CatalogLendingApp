# *************************************************************************************
# *  REFERENCES
# *  Title: Implementing Multiple File Uploads in Django
# *  Author: Pwaveino Clarkson
# *  Date: Jul 18, 2023
# *  URL: https://medium.com/django-unleashed/implementing-multiple-file-uploads-in-django-e9b1833755ed
# *
# *  Title: Django Forms
# *  URL: https://www.geeksforgeeks.org/django-forms/
# *
# *************************************************************************************

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from django.core.paginator import Paginator
from .forms import SearchForm, EquipmentEditForm, ProfileEditForm
from .models import UserProfile
from .models import Equipment
from .models import Collection
from django.contrib import messages
from .models import EquipmentImage


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
        context = {"form": form}
        return render(request, 'home.html', context)
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

@login_required
def item_detail(request, item_id):
    item = get_object_or_404(Equipment, id=item_id)
    is_librarian = hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'librarian'
    edit_form = None

    if is_librarian:
        if request.method == 'POST':
            form = EquipmentEditForm(request.POST, request.FILES, instance=item)
            if form.is_valid():
                equipment = form.save()
                
                images = request.FILES.getlist('images')
                if images:
                    equipment.images.all().delete()
                    
                    for image in images:
                        EquipmentImage.objects.create(
                            equipment=equipment,
                            image=image,
                            is_primary=not equipment.images.exists()
                        )
                
                messages.success(request, 'Equipment updated successfully!')
                return redirect('item_detail', item_id=item.id)
        else:
            edit_form = EquipmentEditForm(instance=item)

    return render(request, 'item_detail.html', {
        'item': item,
        'edit_form': edit_form if is_librarian else None,
        'is_librarian': is_librarian,
    })

def collection_detail(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    if not collection.can_user_access(request.user):
        return redirect('home')
    
    equipment_items = collection.equipment_items.all()
    
    return render(request, 'collection_detail.html', {
        'collection': collection,
        'equipment_items': equipment_items,
        'collection_id': collection_id
    })

def search_results(req):
    form = SearchForm(req.GET)
    query = req.GET.get('query', '')
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

@login_required
def profile_detail(request):
    profile = request.user.userprofile
    edit_form = None

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile_detail')
    else:
        edit_form = ProfileEditForm(instance=profile)

    return render(request, 'profile_detail.html', {
        'profile': profile,
        'edit_form': edit_form,
        'google_account': request.user.email
    })