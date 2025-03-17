from .forms import SearchForm
from .models import Collection

def search_form(request):
    collections = Collection.objects.filter(is_public=True)
    return {
        'form': SearchForm(),
        'collections': collections
    }