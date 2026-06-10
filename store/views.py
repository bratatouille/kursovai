from django.shortcuts import render, get_object_or_404
from .models import ProductLine, Category, Product, Specification, ProductSpec
from collections import defaultdict
from decimal import Decimal
from django.urls import reverse
# Create your views here.
def index(request):
    return render(request, 'store/index.html')

def catalog(request):
    product_lines = ProductLine.objects.all()
    return render(request, 'store/catalog.html', {'product_lines': product_lines})

def category_detail(request, product_line_slug, category_slug):
    product_line = get_object_or_404(ProductLine, slug=product_line_slug)
    category = get_object_or_404(Category, slug=category_slug, product_line=product_line)
    
    # Получаем все продукты категории с предзагрузкой изображений
    products = category.products.prefetch_related('images')
    
    # Получаем параметры фильтрации
    price_from = request.GET.get('price_from')
    price_to = request.GET.get('price_to')
    
    # Фильтрация по цене
    if price_from:
        try:
            price_from_decimal = Decimal(price_from)
            # Фильтруем товары, у которых финальная цена >= price_from
            filtered_products = []
            for product in products:
                if product.final_price >= price_from_decimal:
                    filtered_products.append(product.id)
            products = products.filter(id__in=filtered_products)
        except (ValueError, TypeError):
            pass

    if price_to:
        try:
            price_to_decimal = Decimal(price_to)
            # Фильтруем товары, у которых финальная цена <= price_to
            filtered_products = []
            for product in products:
                if product.final_price <= price_to_decimal:
                    filtered_products.append(product.id)
            products = products.filter(id__in=filtered_products)
        except (ValueError, TypeError):
            pass
    
    # Получаем все доступные спецификации для продуктов в категории
    specifications = Specification.objects.filter(
        category=category
    ).distinct()
    
    # Собираем доступные значения для каждой спецификации
    filter_options = {}
    selected_specs = defaultdict(list)
    
    for spec in specifications:
        # Получаем все уникальные значения для данной спецификации
        values = ProductSpec.objects.filter(
            specification=spec,
            product__category=category
        ).values_list('value', flat=True).distinct()
        
        filter_options[spec] = sorted(values)
        
        # Проверяем выбранные значения из GET параметров
        selected_values = request.GET.getlist(f'spec_{spec.id}')
        if selected_values:
            selected_specs[spec.id] = selected_values
            # Фильтруем продукты по выбранным спецификациям
            products = products.filter(
                specs__specification=spec,
                specs__value__in=selected_values
            )
    
    # Получаем ID продуктов в корзине и избранном
    cart_product_ids = []
    wishlist_product_ids = []
    if request.user.is_authenticated:
        cart_product_ids = list(request.user.cart_items.values_list('product_id', flat=True))
        wishlist_product_ids = list(request.user.favorite_items.values_list('product_id', flat=True))
    
    return render(request, 'store/category_detail.html', {
        'product_line': product_line,
        'category': category,
        'products': products,
        'filter_options': filter_options,
        'selected_specs': dict(selected_specs),
        'price_from': price_from,
        'price_to': price_to,
        'cart_product_ids': cart_product_ids,
        'wishlist_product_ids': wishlist_product_ids,
    })


def product_detail(request, product_line_slug, category_slug, product_slug):
    product_line = get_object_or_404(ProductLine, slug=product_line_slug)
    category = get_object_or_404(Category, slug=category_slug, product_line=product_line)
    product = get_object_or_404(Product, slug=product_slug, category=category)
    images = product.images.all()
    specs = product.specs.select_related('specification').all()
    cart_product_ids = []
    wishlist_product_ids = []
    if request.user.is_authenticated:
        cart_product_ids = list(request.user.cart_items.values_list('product_id', flat=True))
        wishlist_product_ids = list(request.user.favorite_items.values_list('product_id', flat=True))
    breadcrumbs = [
        ('Каталог', reverse('store:catalog')),
        ('Товары', reverse('store:product_line_detail', args=[product_line.slug])),
        (category.name, reverse('store:category_detail', args=[product_line.slug, category.slug])),
        (product.name, None),
    ]
    return render(request, 'store/product_detail.html', {
        'product': product,
        'images': images,
        'specs': specs,
        'category': category,
        'product_line': product_line,
        'cart_product_ids': cart_product_ids,
        'wishlist_product_ids': wishlist_product_ids,
        'breadcrumbs': breadcrumbs,
    })

def product_line_detail(request, product_line_slug):
    product_line = get_object_or_404(ProductLine, slug=product_line_slug)
    categories = product_line.categories.all()
    products = Product.objects.filter(category__in=categories).prefetch_related('images')
    return render(request, 'store/product_line_detail.html', {
        'product_line': product_line,
        'categories': categories,
        'products': products,
    })
