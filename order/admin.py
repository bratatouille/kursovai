from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'product_price', 'quantity', 'total_price')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('status', 'comment', 'created_at', 'created_by')

    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'total_amount', 'created_at', 'payment_method')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('order_number', 'user__email', 'first_name', 'last_name', 'phone')
    readonly_fields = (
        'order_number', 'user', 'created_at', 'updated_at', 
        'subtotal', 'discount_amount', 'total_amount', 'promocode_used'
    )
    inlines = [OrderItemInline, OrderStatusHistoryInline]

    fieldsets = (
        ('Основная информация', {
            'fields': ('order_number', 'user', 'status', 'created_at')
        }),
        ('Контактная информация', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Адрес доставки', {
            'fields': ('delivery_region', 'delivery_city', 'delivery_street', 
                       'delivery_house', 'delivery_apartment', 'delivery_postal_code')
        }),
        ('Финансы', {
            'fields': ('subtotal', 'discount_amount', 'total_amount', 'promocode_used')
        }),
        ('Прочее', {
            'fields': ('payment_method', 'comment')
        }),
    )

    def save_model(self, request, obj, form, change):
        # Если статус изменился, создаем запись в истории
        if 'status' in form.changed_data:
            OrderStatusHistory.objects.create(
                order=obj,
                status=obj.status,
                comment=f"Статус изменен на '{obj.get_status_display()}' администратором.",
                created_by=request.user
            )
        super().save_model(request, obj, form, change)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'quantity', 'total_price')
    search_fields = ('order__order_number', 'product_name')

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'created_at', 'created_by')
    list_filter = ('status', 'created_at')
    search_fields = ('order__order_number',)
