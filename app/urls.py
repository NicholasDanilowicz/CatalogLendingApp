from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.custom_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path("", views.home, name='home'),
    path("search/", views.search_results, name='search_results'),
    path("select_role/", views.select_role, name='select_role'),
    path("item/<int:item_id>", views.item_detail, name='item_detail')
]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)