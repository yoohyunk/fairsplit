from django.contrib import admin
from .models import Split, Item, SplitParticipant, ItemAssignment

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

@admin.register(ItemAssignment)
class ItemAssignmentAdmin(admin.ModelAdmin):
    list_display = ['split', 'receipt_item', 'participant_count', 'assigned_at']
    list_filter = ['assigned_at', 'split']
    search_fields = ['split__name', 'receipt_item__name']
    readonly_fields = ['assigned_at']
    
    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Participants'

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'split', 'value']
    list_filter = ['split']
    search_fields = ['name', 'description']
