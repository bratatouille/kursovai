from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Q
from .models import (
    ProductLine, Category, Specification, Product, ProductImage, ProductSpec,
    PromoCode, PromoCodeUsage, UserPromoCode
)
from django.utils import timezone
from django.forms import Textarea
from django.db import models
# ===== ОСНОВНЫЕ МОДЕЛИ МАГАЗИНА =====

@admin.register(ProductLine)
class ProductLineAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'image_preview', 'categories_count')
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ('name',)
    readonly_fields = ('image_preview',)
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'image', 'image_preview')
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 80px;" />', obj.image.url)
        return "—"
    image_preview.short_description = 'Превью'

    def categories_count(self, obj):
        return obj.categories.count()
    categories_count.short_description = 'Количество категорий'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_line', 'slug', 'image_preview', 'products_count', 'specifications_count')
    list_filter = ('product_line',)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ('name', 'product_line__name')
    readonly_fields = ('image_preview',)
    fieldsets = (
        (None, {
            'fields': ('product_line', 'name', 'slug', 'image', 'image_preview')
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 80px;" />', obj.image.url)
        return "—"
    image_preview.short_description = 'Превью'

    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = 'Товаров'

    def specifications_count(self, obj):
        return obj.specifications.count()
    specifications_count.short_description = 'Характеристик'


@admin.register(Specification)
class SpecificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'unit', 'products_with_spec_count')
    list_filter = ('category', 'category__product_line')
    search_fields = ('name', 'category__name')

    def products_with_spec_count(self, obj):
        return ProductSpec.objects.filter(specification=obj).count()
    products_with_spec_count.short_description = 'Товаров с характеристикой'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'order', 'is_main', 'image_preview')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 80px; max-width: 120px;" />', obj.image.url)
        return ""
    image_preview.short_description = 'Превью'


class ProductSpecInline(admin.TabularInline):
    model = ProductSpec
    extra = 1
    fields = ('specification', 'value')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "specification":
            # Получаем ID товара из URL
            if request.resolver_match and 'object_id' in request.resolver_match.kwargs:
                try:
                    product_id = request.resolver_match.kwargs['object_id']
                    product = Product.objects.get(pk=product_id)
                    kwargs["queryset"] = Specification.objects.filter(category=product.category)
                except Product.DoesNotExist:
                    pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category', 'is_popular', 'price', 'discount', 'final_price_display', 
        'stock', 'stock_status', 'image_preview'
    )
    list_filter = ('is_popular', 'category', 'discount', 'category__product_line')
    search_fields = ('name', 'description')
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline, ProductSpecInline]
    readonly_fields = ('image_preview', 'final_price_display')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'category', 'is_popular', 'description')
        }),
        ('Цена и скидки', {
            'fields': ('price', 'discount')
        }),
        ('Склад', {
            'fields': ('stock', 'min_stock'),
            'classes': ('collapse',)
        }),
        ('Изображения', {
            'fields': ('image', 'image_preview'),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 150px;" />', obj.image.url)
        return ""
    image_preview.short_description = 'Главное фото'

    def final_price_display(self, obj):
        if obj.pk and obj.final_price is not None:
            return f"{obj.final_price:.2f} ₽"
        return "—"
    final_price_display.short_description = 'Цена со скидкой'

    def stock_status(self, obj):
        if obj.stock == 0:
            return format_html('<span style="color: red;">Нет в наличии</span>')
        elif obj.is_low_stock:
            return format_html('<span style="color: orange;">Заканчивается</span>')
        else:
            return format_html('<span style="color: green;">В наличии</span>')
    stock_status.short_description = 'Статус склада'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'order', 'is_main', 'alt_text', 'image_preview')
    list_filter = ('is_main', 'product__category')
    search_fields = ('alt_text', 'product__name')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 60px; max-width: 90px;" />', obj.image.url)
        return ""
    image_preview.short_description = 'Превью'


@admin.register(ProductSpec)
class ProductSpecAdmin(admin.ModelAdmin):
    list_display = ('product', 'specification', 'value', 'category_display')
    list_filter = ('specification', 'product__category', 'specification__category')
    search_fields = ('value', 'product__name', 'specification__name')

    def category_display(self, obj):
        return obj.product.category.name
    category_display.short_description = 'Категория товара'


# ===== ПРОМОКОДЫ =====

class PromoCodeUsageInline(admin.TabularInline):
    model = PromoCodeUsage
    extra = 0
    readonly_fields = ('user', 'discount_amount', 'order_amount', 'used_at', 'order_id')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'name', 'discount_display', 'status', 'usage_display', 
        'start_date', 'end_date', 'is_active_now', 'is_personal', 'is_email'
    )
    list_filter = ('status', 'discount_type', 'start_date', 'end_date', 'is_personal', 'is_email')
    search_fields = ('code', 'name', 'description')
    readonly_fields = ('used_count', 'created_at', 'updated_at')
    filter_horizontal = ('allowed_users', 'allowed_categories')
    inlines = [PromoCodeUsageInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('code', 'name', 'description', 'status', 'is_personal', 'is_email')
        }),
        ('Скидка', {
            'fields': ('discount_type', 'discount_value', 'max_discount_amount')
        }),
        ('Ограничения', {
            'fields': ('min_order_amount', 'start_date', 'end_date')
        }),
        ('Лимиты использования', {
            'fields': ('usage_limit', 'usage_limit_per_user', 'used_count')
        }),
        ('Доступность', {
            'fields': ('allowed_users', 'allowed_categories'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def discount_display(self, obj):
        if obj.discount_type == 'percent':
            return f"{obj.discount_value}%"
        else:
            return f"{obj.discount_value} ₽"
    discount_display.short_description = 'Скидка'

    def usage_display(self, obj):
        if obj.usage_limit:
            return f"{obj.used_count}/{obj.usage_limit}"
        return f"{obj.used_count}/∞"
    usage_display.short_description = 'Использований'

    def is_active_now(self, obj):
        now = timezone.now()
        is_active = (
            obj.status == 'active' and
            obj.start_date <= now <= obj.end_date and
            (not obj.usage_limit or obj.used_count < obj.usage_limit)
        )
        color = 'green' if is_active else 'red'
        text = 'Да' if is_active else 'Нет'
        return format_html(
            '<span style="color: {};">{}</span>',
            color, text
        )
    is_active_now.short_description = 'Активен сейчас'

    actions = ['activate_promocodes', 'deactivate_promocodes', 'reset_usage_count']

    def activate_promocodes(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'Активировано {updated} промокодов.')
    activate_promocodes.short_description = 'Активировать выбранные промокоды'

    def deactivate_promocodes(self, request, queryset):
        updated = queryset.update(status='inactive')
        self.message_user(request, f'Деактивировано {updated} промокодов.')
    deactivate_promocodes.short_description = 'Деактивировать выбранные промокоды'

    def reset_usage_count(self, request, queryset):
        updated = queryset.update(used_count=0)
        self.message_user(request, f'Сброшен счетчик использований для {updated} промокодов.')
    reset_usage_count.short_description = 'Сбросить счетчик использований'


@admin.register(PromoCodeUsage)
class PromoCodeUsageAdmin(admin.ModelAdmin):
    list_display = ('promocode', 'user', 'discount_amount', 'order_amount', 'used_at', 'order_id')
    list_filter = ('promocode', 'used_at')
    search_fields = ('promocode__code', 'user__email', 'order_id')
    readonly_fields = ('used_at',)
    
    def has_add_permission(self, request):
        return False  # Запрещаем создание через админку
    
    def has_change_permission(self, request, obj=None):
        return False  # Запрещаем изменение через админку


@admin.register(UserPromoCode)
class UserPromoCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'promocode', 'assigned_at', 'assigned_by', 'is_notified')
    list_filter = ('promocode', 'assigned_at', 'is_notified')
    search_fields = ('user__email', 'promocode__code')
    readonly_fields = ('assigned_at',)
    
    def save_model(self, request, obj, form, change):
        if not change:  # Если создается новый объект
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)