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
    path("item/<int:item_id>", views.item_detail, name='item_detail'),
    path("item/create/", views.create_equipment, name='create_equipment'),
    path("item/<int:item_id>/edit/", views.edit_equipment, name='edit_equipment'),
    path("item/<int:item_id>/delete/", views.delete_equipment, name='delete_equipment'),
    path("collection/<int:collection_id>/", views.collection_detail, name='collection_detail'),
    path("collection/create/", views.create_collection, name='create_collection'),
    path("collection/<int:collection_id>/edit/", views.edit_collection, name='edit_collection'),
    path("collection/<int:collection_id>/delete/", views.delete_collection, name='delete_collection'),
    path("profile/", views.profile_detail, name='profile_detail'),
    path("request/<int:request_id>/<str:action>", views.handle_request, name='handle_request'),
    path("request-access/<int:collection_id>/", views.request_access, name='request_access')
]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)