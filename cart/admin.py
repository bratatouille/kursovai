from django.contrib import admin
from .models import CartItem, CartPromoCode

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'added_at', 'total_price')
    list_filter = ('user', 'product__category', 'added_at')
    search_fields = ('user__email', 'product__name')
    readonly_fields = ('total_price',)

    def total_price(self, obj):
        return obj.total_price
    total_price.short_description = 'Общая стоимость'

@admin.register(CartPromoCode)
class CartPromoCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'promocode', 'applied_at')
    search_fields = ('user__email', 'promocode__code')
