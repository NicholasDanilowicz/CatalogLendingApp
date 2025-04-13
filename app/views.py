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

from .forms import SearchForm, EquipmentForm, ProfileEditForm, CollectionCreateForm, CollectionEditForm
from .models import UserProfile
from .models import Equipment
from .models import Collection
from django.contrib import messages
from .models import Rental
from .models import RentalRequest
from .models import Rating
from .utils import handle_equipment_images
from .auth_utils import is_librarian




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
    equipment = get_object_or_404(Equipment, id=item_id)
    is_librarian_user = is_librarian(request.user)
    rental = Rental.objects.filter(equipment=equipment, user=request.user, returned_on__isnull=True).first()
    pending_request = RentalRequest.objects.filter(equipment=equipment, patron=request.user, status='pending').first()

    if request.method == 'POST':
        if rental:
            rental.returned_on = timezone.now()
            rental.save()
            equipment.available = True
            equipment.save()
            messages.success(request, f"Thank you for returning {equipment.name}.")
            return redirect('item_detail', item_id=item_id)

        if pending_request:
            pending_request.delete()
            messages.info(request, "Your request has been canceled.")
            return redirect('item_detail', item_id=item_id)

        if not equipment.available:
            messages.error(request, "This item is currently unavailable.")
            return redirect('item_detail', item_id=item_id)

        RentalRequest.objects.create(equipment=equipment, patron=request.user)
        messages.success(request, f"You have requested {equipment.name}. Await librarian approval.")
        return redirect('item_detail', item_id=item_id)

    return render(request, 'item_detail.html', {
        'item': equipment,
        'is_librarian': is_librarian_user,
        'rental': rental,
        'pending_request': pending_request,
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
        'is_librarian': is_librarian(request.user),
        'is_patron': request.user.userprofile.role == 'patron'
    })

@login_required
def edit_collection(request, collection_id):
    if not is_librarian(request.user):
        messages.error(request, "Only librarians can edit collections.")
        return redirect('home')
        
    collection = get_object_or_404(Collection, id=collection_id)
    
    if collection.creator != request.user:
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
        'is_librarian': is_librarian(request.user)
    })

@login_required
def delete_collection(request, collection_id):
    if not is_librarian(request.user):
        messages.error(request, "Only librarians can delete collections.")
        return redirect('home')
        
    collection = get_object_or_404(Collection, id=collection_id)
    
    if collection.creator != request.user:
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
    if not is_librarian(request.user):
        messages.error(request, "Only librarians can create equipment.")
        return redirect('home')
        
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES)
        if form.is_valid():
            equipment = form.save()
            images = request.FILES.getlist('images')
            handle_equipment_images(equipment, images)
            messages.success(request, 'Equipment created successfully!')
            return redirect('item_detail', item_id=equipment.id)
    else:
        form = EquipmentForm()
    
    return render(request, 'create_equipment.html', {
        'form': form
    })

@login_required
def edit_equipment(request, item_id):
    if not is_librarian(request.user):
        messages.error(request, "Only librarians can edit equipment.")
        return redirect('home')
        
    equipment = get_object_or_404(Equipment, id=item_id)
    
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES, instance=equipment)
        if form.is_valid():
            equipment = form.save()
            images = request.FILES.getlist('images')
            handle_equipment_images(equipment, images)
            messages.success(request, 'Equipment updated successfully!')
            return redirect('item_detail', item_id=equipment.id)
    else:
        form = EquipmentForm(instance=equipment)
    
    return render(request, 'edit_equipment.html', {
        'form': form,
        'item': equipment
    })

@login_required
def delete_equipment(request, item_id):
    if not is_librarian(request.user):
        messages.error(request, "Only librarians can delete equipment.")
        return redirect('home')
        
    equipment = get_object_or_404(Equipment, id=item_id)
    
    if request.method == 'POST':
        equipment.delete()
        messages.success(request, 'Equipment deleted successfully!')
        return redirect('home')
    
    return render(request, 'delete_equipment.html', {
        'equipment': equipment
    })

@login_required
def handle_request(request, request_id, action):
    access_request = get_object_or_404(CollectionAccessRequest, id=request_id)

    if not is_librarian(request.user) or access_request.collection.creator != request.user:
        messages.error(request, 'You are not authoriazed to manage this request.')
        return redirect('collection_detail', collection_id=access_request.collection.id)
    if action == 'accept':
        access_request.status = 'accepted'
        access_request.collection.allowed_users.add(access_request.patron)
        messages.success(request, "Access request accepted.")
    elif action == 'deny':
        access_request.status = 'denied'
        messages.warning(request, "Access request denied.")
    access_request.save()
    return redirect('collection_detail', collection_id=access_request.collection.id)

from .models import CollectionAccessRequest
def collection_detail(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    has_access = collection.can_user_access(request.user)
    
    if not has_access and request.user.userprofile.role == 'patron':
        existing_request = CollectionAccessRequest.objects.filter(collection=collection, patron=request.user, status='pending').exists()
        if request.method == 'POST' and 'request_access' in request.POST:
            if existing_request:
                messages.info(request, "You have already requested access to this collection.")
            else:
                CollectionAccessRequest.objects.create(
                    collection=collection,
                    patron=request.user,
                    status='pending'
                )
                messages.success(request, "Your access request has been submitted.")
            return redirect('collection_detail', collection_id=collection_id)
    access_requests = []

    if request.user.userprofile.role == 'librarian' and collection.creator == request.user:
        access_requests = collection.access_requests.filter(status='pending')
    
    lol = request.user.userprofile.role
    if len(access_requests) == 0:
        lol = "NOT FUCKING WORKING"
    context = {
        'collection': collection,
        'has_access': has_access,
        'collection_id': collection_id,
        'access_requests': access_requests,
        'sum_shit': lol
    }
    
    if has_access:
        equipment_items = collection.equipment_items.all()
        context['equipment_items'] = equipment_items
    
    return render(request, 'collection_detail.html', context)
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
@login_required
# @csrf_exempt
def request_access(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    print("this is getting hit")
    if CollectionAccessRequest.objects.filter(patron=request.user, collection=collection).exists():
        messages.warning(request, "You have already requested access to this collection.")
        return HttpResponse("PROCESSING REQUEST YOU HAVE ALREADY REQUESTED ACCESS????")
    else:
        CollectionAccessRequest.objects.create(patron=request.user, collection=collection)
        messages.success(request, "Access request submitted.")
        return HttpResponse("PROCESSING REQUEST GOOD FIRST TIME???")
    
    # return redirect('collection_detail', collection_id=collection.id)
# def request_access(request, collection_id):
#     if request.method == 'POST':
#         collection = get_object_or_404(Collection, id=collection_id)
#         CollectionAccessRequest.objects.get_or_create(patron=request.user, collection=collection)
#         messages.success(request, 'Access request submitted.')
#         return redirect('collection_detail', collection_id=collection.id)

@login_required
def rental_detail(request):
    active_rentals = Rental.objects.filter(user=request.user, returned_on__isnull=True)
    return render(request, 'rental_detail.html', {'rentals': active_rentals})

@login_required
def rate_equipment(request, item_id):
        if request.method == 'POST':
            rating = int(request.POST.get('rating'))
            if 1 <= rating <= 5:
                item = get_object_or_404(Equipment, id=item_id)
                rating, created = Rating.objects.get_or_create(
                    equipment=item,
                    user=request.user,
                    defaults={'rating': rating}
                )

        return redirect('item_detail', item_id=item_id)


@login_required
def request_rental(request, equipment_id):
    equipment = get_object_or_404(Equipment, id=equipment_id)

    if RentalRequest.objects.filter(equipment=equipment, patron=request.user, status='pending').exists():
        return redirect('item_detail', equipment_id=equipment.id)

    RentalRequest.objects.create(equipment=equipment, patron=request.user)
    return redirect('rental_detail')


@login_required
def rental_requests_view(request):
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')

        rental_request = get_object_or_404(RentalRequest, id=request_id)

        if rental_request.status != 'pending':
            messages.warning(request, "This request has already been processed.")
            return redirect('rental_requests')

        if action == 'approve':
            if not rental_request.equipment.available:
                messages.error(request, "This equipment is no longer available.")
                rental_request.status = 'denied'
                rental_request.save()
                return redirect('rental_requests')

            rental_request.status = 'approved'
            rental_request.save()

            Rental.objects.create(
                equipment=rental_request.equipment,
                user=rental_request.patron,
                return_by=timezone.now() + timezone.timedelta(days=7)
            )

            rental_request.equipment.available = False
            rental_request.equipment.save()

            RentalRequest.objects.filter(
                equipment=rental_request.equipment,
                status='pending'
            ).exclude(id=rental_request.id).update(status='denied')

            messages.success(request, f"Rental approved for {rental_request.patron.username}.")
        elif action == 'deny':
            rental_request.status = 'denied'
            rental_request.save()
            messages.info(request, f"Rental denied for {rental_request.patron.username}.")

        return redirect('rental_requests')

    requests = RentalRequest.objects.filter(status='pending').select_related('equipment', 'patron')
    return render(request, 'rental_requests.html', {'requests': requests})