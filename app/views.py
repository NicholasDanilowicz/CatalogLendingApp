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

from .forms import SearchForm, EquipmentForm, ProfileEditForm, CollectionCreateForm, CollectionEditForm, \
    PutItemInPublicCollectionForm, CommentForm
from .models import UserProfile
from .models import Equipment
from .models import Collection
from django.db.models import Avg
from django.contrib import messages
from .models import Rental
from .models import RentalRequest
from .models import Rating
from .models import Comment
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



def item_detail(request, item_id):
    private_collections = Collection.objects.filter(is_public=False)
    equipment = get_object_or_404(Equipment, id=item_id)

    if request.user.is_authenticated:
        is_librarian_user = is_librarian(request.user)
        rental = Rental.objects.filter(equipment=equipment, user=request.user, returned_on__isnull=True).first()
        pending_request = RentalRequest.objects.filter(equipment=equipment, patron=request.user, status='pending').first()
        user_rating = Rating.objects.filter(equipment=equipment, user=request.user).first()
        has_rented = Rental.objects.filter(equipment=equipment, user=request.user).exists()
        user = request.user
        public_collections_by_user = Collection.objects.filter(creator=request.user, is_public=True)
    else:
        is_librarian_user = False
        rental = None
        pending_request = None
        user_rating = None
        has_rented = False
        user = None
        public_collections_by_user = None

# ***************************************************************************************
# *  REFERENCES
# *  Title: Debugging Django Code Errors with ChatGPT
# *  Author: OpenAI (ChatGPT)
# *  Date: 2025
# *  Code version: GPT-4o
# *  URL: https://chat.openai.com/
# *  Software License: OpenAI Terms of Use
# *  Description: Used to debug Django form errors while developing functionality for rental requests.
# ***************************************************************************************

    if request.method == 'POST':
        if 'content' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.user = request.user
                comment.item = equipment
                comment.save()
                messages.success(request, "Your comment has been posted.")
                return redirect('item_detail', item_id=item_id)
        else:
            comment_form = CommentForm()

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
    else:
        comment_form = CommentForm()

    # Average rating calculations and comments
    average_rating = Rating.objects.filter(equipment=equipment).aggregate(Avg('rating'))['rating__avg'] or 0
    comments = Comment.objects.filter(item=equipment).order_by('-created_at')

    return render(request, 'item_detail.html', {
        'item': equipment,
        'is_librarian': is_librarian_user,
        'rental': rental,
        'public_collections_by_user': public_collections_by_user,
        'user': user,
        'pending_request': pending_request,
        'user_rating': user_rating,
        'average_rating': average_rating,
        'has_rented': has_rented,
        'comments': comments,
        'comment_form': comment_form,
    })


def search_results(req):
    form = SearchForm(req.GET)
    query = req.GET.get('query', '')
    collection_id = req.GET.get('collection_id')
    tag = req.GET.get('tag')
    
    public_collections = Collection.objects.filter(is_public=True)
    base_queryset = Equipment.objects.filter(collections__in=public_collections).distinct().order_by('id')

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

    paginator = Paginator(base_queryset, 15)
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
    collection = get_object_or_404(Collection, id=collection_id)
    
    if not is_librarian(request.user) and collection.creator != request.user:
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
    collection = get_object_or_404(Collection, id=collection_id)
    
    if not is_librarian(request.user) and collection.creator != request.user:
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

    if not is_librarian(request.user):
        messages.error(request, 'You are not authorized to manage this request.')
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
    
    if not request.user.is_authenticated and not collection.is_public:
        messages.error(request, "You must be logged in to view this collection.")
        return redirect('login')
    
    has_access = collection.can_user_access(request.user)
    
    if not has_access and request.user.is_authenticated and request.user.userprofile.role == 'patron':
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

    if request.user.is_authenticated and request.user.userprofile.role == 'librarian':
        access_requests = collection.access_requests.filter(status='pending')
    
    context = {
        'collection': collection,
        'has_access': has_access,
        'collection_id': collection_id,
        'access_requests': access_requests,
    }
    
    if has_access:
        equipment_items = collection.equipment_items.all().order_by('id')
        paginator = Paginator(equipment_items, 15)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
    
    return render(request, 'collection_detail.html', context)
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
@login_required
# @csrf_exempt
def request_access(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    
    if collection.is_public:
        messages.warning(request, "This is a public collection. No access request needed.")
        return redirect('collection_detail', collection_id=collection.id)
    
    if collection.can_user_access(request.user):
        messages.info(request, "You already have access to this collection.")
        return redirect('collection_detail', collection_id=collection.id)
    
    existing_request = CollectionAccessRequest.objects.filter(
        patron=request.user,
        collection=collection,
        status='pending'
    ).exists()
    
    if existing_request:
        messages.warning(request, "You have already requested access to this collection.")
    else:
        CollectionAccessRequest.objects.create(
            patron=request.user,
            collection=collection,
            status='pending'
        )
        messages.success(request, "Access request submitted successfully.")
    
    return redirect('collection_detail', collection_id=collection.id)

@login_required
def put_item_in_public_collection(request, item_id):
    equipment = get_object_or_404(Equipment, id=item_id)

    if request.method == 'POST':
        form = PutItemInPublicCollectionForm(request.POST, request.FILES, instance=equipment, user=request.user)
        if form.is_valid():
            equipment = form.save()
            messages.success(request, 'Item added to public collection(s) successfully!')
            return redirect('item_detail', item_id=equipment.id)
    else:
        form = PutItemInPublicCollectionForm(instance=equipment, user=request.user)

    return render(request, 'put_in_public_collection.html', {
        'item': equipment,
        'form': form,
    })
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
            try:
                rating_value = int(request.POST.get('rating'))
            except (TypeError, ValueError):
                messages.error(request, "Invalid rating value.")
                return redirect('item_detail', item_id=item_id)

            if 1 <= rating_value <= 5:
                equipment = get_object_or_404(Equipment, id=item_id)
                has_rented = Rental.objects.filter(equipment=equipment, user=request.user).exists()

                if not has_rented:
                    messages.error(request, "You can only review items you have rented.")
                    return redirect('item_detail', item_id=item_id)

                rating_obj, created = Rating.objects.get_or_create(
                    equipment=equipment,
                    user=request.user,
                    defaults={'rating': rating_value}
                )
                if not created:
                    rating_obj.rating = rating_value
                    rating_obj.save()
                messages.success(request, "Your rating has been saved.")
            else:
                messages.error(request, "Rating must be between 1 and 5.")

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


def home(request):
    featured_collections = Collection.objects.filter(is_public=True).order_by('-created_at')[:6]
    return render(request, 'home.html', {
        'featured_collections': featured_collections,
    })
