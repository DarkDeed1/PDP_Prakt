from django.contrib import admin

from .models import AuditLog, Counterparty, Deal, DealStatusHistory, Interaction


@admin.register(Counterparty)
class CounterpartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'counterparty_type', 'inn', 'contact_person', 'phone', 'is_archived')
    search_fields = ('name', 'short_name', 'inn', 'contact_person', 'email')
    list_filter = ('counterparty_type', 'is_archived')


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('title', 'counterparty', 'status', 'priority', 'amount', 'control_date', 'responsible')
    search_fields = ('title', 'counterparty__name', 'counterparty__inn')
    list_filter = ('status', 'priority', 'is_archived')


@admin.register(DealStatusHistory)
class DealStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('deal', 'old_status', 'new_status', 'changed_by', 'changed_at')
    list_filter = ('new_status', 'changed_at')


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('subject', 'counterparty', 'deal', 'interaction_type', 'interaction_date', 'created_by')
    search_fields = ('subject', 'counterparty__name', 'deal__title')
    list_filter = ('interaction_type', 'interaction_date')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'action', 'model_name', 'object_repr', 'ip_address')
    search_fields = ('object_repr', 'details', 'user__username')
    list_filter = ('action', 'model_name', 'created_at')
