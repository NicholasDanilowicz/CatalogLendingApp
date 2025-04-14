from .forms import SearchForm
from .models import Collection

def search_form(request):
    if request.user.is_authenticated:
        all_collections = Collection.objects.all()
        collections = [collection for collection in all_collections if collection.can_user_access(request.user)]
    else:
        collections = Collection.objects.filter(is_public=True)
    return {
        'search_form': SearchForm(),
        'collections': collections
    }

def user_profile(request):
    if request.user.is_authenticated:
        return {'profile': request.user.userprofile}
    return {}