from django.contrib import admin
from .models import Split, Item, SplitParticipant

@admin.register(Split)
class SplitAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'status', 'currency', 'date_created']
    list_filter = ['status', 'currency', 'date_created']
    search_fields = ['name', 'description', 'user__email']
    readonly_fields = ['date_created']

@admin.register(SplitParticipant)
class SplitParticipantAdmin(admin.ModelAdmin):
    list_display = ['email', 'split', 'user', 'agreed', 'joined_at']
    list_filter = ['agreed', 'joined_at']
    search_fields = ['email', 'split__name']
    readonly_fields = ['joined_at']

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'split', 'value']
    list_filter = ['split']
    search_fields = ['name', 'description']
