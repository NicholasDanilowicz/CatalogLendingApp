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
from django.contrib.auth import logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from django.core.paginator import Paginator
from django.utils import timezone

from .forms import SearchForm, EquipmentEditForm, ProfileEditForm, CollectionCreateForm, CollectionEditForm, EquipmentCreateForm
from .models import UserProfile
from .models import Equipment
from .models import Collection
from django.contrib import messages
from .models import EquipmentImage, Rental


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

    equipment = get_object_or_404(Equipment, id=item_id)
    rental = Rental.objects.filter(equipment=equipment, user=request.user, returned_on__isnull=True).first()

    if request.method == 'POST':
        if rental:
            rental.returned_on = timezone.now()
            rental.save()

            equipment.available = True
            equipment.save()

            messages.success(request, f"Thank you for returning {equipment.name}.")
            return redirect('item_detail', item_id=item_id)
        else:
            if not equipment.available:
                messages.error(request, "This item is currently unavailable.")
                return redirect('item_detail', item_id=item_id)

            equipment.available = False
            equipment.save()

            rental = Rental.objects.create(
                equipment=equipment,
                user=request.user,
                return_by=timezone.now() + timezone.timedelta(days=7),
            )

            messages.success(request, f"You have rented {equipment.name}. Please return it by {rental.return_by}.")
            return redirect('item_detail', item_id=item_id)

    return render(request, 'item_detail.html', {
        'item': item,
        'edit_form': edit_form if is_librarian else None,
        'is_librarian': is_librarian,
        'rental': rental,

    })

def collection_detail(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    has_access = collection.can_user_access(request.user)
    
    context = {
        'collection': collection,
        'has_access': has_access,
        'collection_id': collection_id
    }
    
    if has_access:
        equipment_items = collection.equipment_items.all()
        context['equipment_items'] = equipment_items
    
    return render(request, 'collection_detail.html', context)

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
        if request.POST.get('action') == 'logout':
            logout(request)
            return redirect('home')
        else:
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

@login_required
def create_collection(request):
    if request.method == 'POST':
        form = CollectionCreateForm(request.POST, user=request.user)
        if form.is_valid():
            collection = form.save(commit=False)
            collection.creator = request.user
            collection = form.save()
            messages.success(request, 'Collection created!')
            return redirect('collection_detail', collection_id=collection.id)
    else:
        form = CollectionCreateForm(user=request.user)
    
    return render(request, 'create_collection.html', {
        'form': form,
        'is_librarian': request.user.userprofile.role == 'librarian',
        'is_patron': request.user.userprofile.role == 'patron'
    })

@login_required
def edit_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    
    if collection.creator != request.user and request.user.userprofile.role != 'librarian':
        messages.error(request, "You don't have permission to edit this collection.")
        return redirect('collection_detail', collection_id=collection_id)
    
    if request.method == 'POST':
        form = CollectionEditForm(request.POST, instance=collection, user=request.user)
        if form.is_valid():
            collection = form.save()
            messages.success(request, 'Collection updated successfully!')
            return redirect('collection_detail', collection_id=collection.id)
    else:
        form = CollectionEditForm(instance=collection, user=request.user)
    
    return render(request, 'edit_collection.html', {
        'form': form,
        'collection': collection,
        'is_librarian': request.user.userprofile.role == 'librarian'
    })

@login_required
def delete_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    
    if collection.creator != request.user and request.user.userprofile.role != 'librarian':
        messages.error(request, "You don't have permission to delete this collection.")
        return redirect('collection_detail', collection_id=collection_id)
    
    if request.method == 'POST':
        collection.delete()
        messages.success(request, 'Collection deleted successfully!')
        return redirect('home')
    
    return render(request, 'delete_collection.html', {
        'collection': collection
    })

@login_required
def create_equipment(request):
    if not request.user.userprofile.role == 'librarian':
        messages.error(request, "Only librarians can create equipment.")
        return redirect('home')
        
    if request.method == 'POST':
        form = EquipmentCreateForm(request.POST, request.FILES)
        if form.is_valid():
            equipment = form.save()
            
            images = request.FILES.getlist('images')
            if images:
                for image in images:
                    EquipmentImage.objects.create(
                        equipment=equipment,
                        image=image,
                        is_primary=not equipment.images.exists()
                    )
            
            messages.success(request, 'Equipment created successfully!')
            return redirect('item_detail', item_id=equipment.id)
    else:
        form = EquipmentCreateForm()
    
    return render(request, 'create_equipment.html', {
        'form': form
    })

@login_required
def delete_equipment(request, item_id):
    if not request.user.userprofile.role == 'librarian':
        messages.error(request, "Only librarians can delete equipment.")
        return redirect('item_detail', item_id=item_id)
        
    equipment = get_object_or_404(Equipment, id=item_id)
    
    if request.method == 'POST':
        equipment.delete()
        messages.success(request, 'Equipment deleted successfully!')
        return redirect('home')
    
    return render(request, 'delete_equipment.html', {
        'equipment': equipment
    })