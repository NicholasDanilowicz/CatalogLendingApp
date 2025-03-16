from django.contrib import admin
from .models import Collection, Equipment, UserProfile

class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'available')

admin.site.register(Collection)
admin.site.register(Equipment, EquipmentAdmin)
admin.site.register(UserProfile) 