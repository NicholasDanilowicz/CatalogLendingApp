from .forms import SearchForm
from .models import Collection

def search_form(request):
    if request.user.is_authenticated:
        collections = Collection.objects.all()
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