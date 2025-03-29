from .forms import SearchForm
from .models import Collection

def search_form(request):
    collections = Collection.objects.filter(is_public=True)
    return {
        'form': SearchForm(),
        'collections': collections
    }

def user_profile(request):
    if request.user.is_authenticated:
        return {'profile': request.user.userprofile}
    return {}