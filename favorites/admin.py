from django.contrib import admin
from .models import FavoriteItem

@admin.register(FavoriteItem)
class FavoriteItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')
    list_filter = ('added_at', 'product__category')
    search_fields = ('user__email', 'product__name')
