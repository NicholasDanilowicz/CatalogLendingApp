from django.contrib import admin
from .models import Collection, Equipment, UserProfile, CollectionAccessRequest
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

class CollectionAccessRequestAdmin(admin.ModelAdmin):
    list_display = ('patron', 'collection', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('patron__username', 'collection__title')
    readonly_fields = ('created_at',)

admin.site.register(Equipment, EquipmentAdmin)
admin.site.register(Collection, CollectionAdmin)
admin.site.register(UserProfile)
admin.site.register(CollectionAccessRequest, CollectionAccessRequestAdmin)