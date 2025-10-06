from django.contrib import admin
from .models import PaymentRequest

@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ('reference_no', 'email', 'amount', 'status', 'payment_channel', 'created_at', 'paid_at')
    list_filter = ('status', 'payment_channel', 'currency', 'created_at')
    search_fields = ('reference_no', 'email', 'user_id', 'transaction_id')
    readonly_fields = ('reference_no', 'created_at', 'paid_at')
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('reference_no', 'amount', 'currency', 'status')
        }),
        ('Customer Details', {
            'fields': ('user_id', 'email', 'phone', 'description')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'payment_channel', 'transaction_id', 'authorization_url', 'access_code')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at', 'paid_at')
        }),
        ('Additional Data', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by('-created_at')
    
    # Color-code status
    def status(self, obj):
        colors = {
            'paid': 'green',
            'pending': 'orange',
            'failed': 'red',
            'expired': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return f'<span style="color: {color}; font-weight: bold;">{obj.status.upper()}</span>'
    
    status.allow_tags = True
