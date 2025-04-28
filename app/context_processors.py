from .forms import SearchForm
from .models import Collection
from .models import UserProfile

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
        try:
            return {'profile': request.user.userprofile}
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user, role='patron')
            return {'profile': profile}
    return {}