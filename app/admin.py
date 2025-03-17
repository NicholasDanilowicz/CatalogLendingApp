from django.contrib import admin
from .models import Collection, Equipment, UserProfile
from .forms import CollectionAdminForm

class CollectionAdmin(admin.ModelAdmin):
    form = CollectionAdminForm
    list_display = ('title', 'tags', 'is_public')
    list_filter = ('is_public',)
    search_fields = ('title',)
    filter_horizontal = ('allowed_users',)

class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'available')
    list_filter = ('available',)
    search_fields = ('name', 'description')
    filter_horizontal = ('collections',)

admin.site.register(Equipment, EquipmentAdmin)
admin.site.register(Collection, CollectionAdmin)
admin.site.register(UserProfile)