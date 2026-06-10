from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from store.models import Category, Product, ProductSpec
from .models import PCBuild, PCBuildComponent, SavedPCBuild, CompatibilityRule, CategoryPC, PrebuiltPC, PrebuiltPCComponent
from django.db import transaction
import json
from django.views.decorators.csrf import csrf_exempt



@login_required
def configurator(request):
    return render(request, 'pcbuilder/configurator.html')

@require_GET
@login_required
def api_categories(request):
    categories = Category.objects.filter(slug__in=Category.PROTECTED_SLUGS).values('id', 'name', 'slug')
    categories_data = sorted(categories, key=lambda x: x['id'])
    return JsonResponse({'categories': list(categories_data)})

@require_GET
@login_required
def api_category_filters(request):
    """Получение доступных фильтров для категории"""
    category_id = request.GET.get('category')
    if not category_id:
        return JsonResponse({'filters': []})
    
    try:
        category = get_object_or_404(Category, id=category_id)
        
        # Получаем спецификации для данной категории
        specifications = category.specifications.all()
        
        filters = []
        for spec in specifications:
            # Получаем уникальные значения для каждой спецификации
            values = ProductSpec.objects.filter(
                specification=spec,
                product__category=category
            ).values_list('value', flat=True).distinct()
            
            if values:  # Только если есть значения
                filters.append({
                    'id': spec.id,
                    'name': spec.name,
                    'unit': spec.unit,
                    'values': sorted(list(values))
                })
        
        return JsonResponse({'filters': filters})
        
    except Category.DoesNotExist:
        return JsonResponse({'filters': []})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_GET
@login_required
def api_products(request):
    """Получение товаров с фильтрацией"""
    category_id = request.GET.get('category')
    filter1_spec = request.GET.get('filter1_spec')  # ID спецификации
    filter1_value = request.GET.get('filter1_value')  # Значение
    filter2_spec = request.GET.get('filter2_spec')
    filter2_value = request.GET.get('filter2_value')
    compatible_only = request.GET.get('compatible_only') == '1'
    
    if not category_id:
        return JsonResponse({'products': []})
    
    products = Product.objects.filter(category_id=category_id)
    
    # Применяем фильтры
    if filter1_spec and filter1_value:
        products = products.filter(
            specs__specification_id=filter1_spec,
            specs__value=filter1_value
        )
    
    if filter2_spec and filter2_value:
        products = products.filter(
            specs__specification_id=filter2_spec,
            specs__value=filter2_value
        )
    
    # Получаем выбранные продукты для текущей сборки пользователя
    build, _ = PCBuild.objects.get_or_create(user=request.user)
    selected_product_ids = set(build.components.values_list('product_id', flat=True))
    
    # Фильтрация по совместимости
    if compatible_only:
        compatible_products = []
        for product in products.distinct():
            # Проверяем совместимость с текущей сборкой
            ok, _ = check_compatibility(build, product)
            if ok:
                compatible_products.append(product)
        products = compatible_products
    else:
        products = products.distinct()
    
    result = []
    for product in products:
        specs = list(product.specs.select_related('specification').values(
            'specification__name', 'value', 'specification__unit'))
        result.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'discount': float(product.discount),
            'image': product.image.url if product.image else '',
            'specs': specs,
            'is_selected': product.id in selected_product_ids,
            'product_line_slug': product.category.product_line.slug,
            'category_slug': product.category.slug,
            'product_slug': product.slug,
            'stock': product.stock,
        })
    
    return JsonResponse({'products': result})

@login_required
def api_build(request):
    build, _ = PCBuild.objects.get_or_create(user=request.user)
    components = build.components.select_related('product', 'category')
    result = []
    total = 0
    for comp in components:
        final_price = comp.product.final_price
        result.append({
            'category_id': comp.category.id,
            'category_name': comp.category.name,
            'product_id': comp.product.id,
            'product_name': comp.product.name,
            'price': float(comp.product.price),
            'discount': comp.product.discount,
            'image': comp.product.image.url if comp.product.image else '',
            'quantity': comp.quantity,
        })
        total += final_price * comp.quantity
    return JsonResponse({'components': result, 'total': float(total)})

@require_POST
@login_required
def api_build_add(request):
    data = json.loads(request.body)
    product_id = data.get('product_id')
    if not product_id:
        return JsonResponse({'success': False, 'error': 'Нет product_id'}, status=400)
    product = get_object_or_404(Product, id=product_id)
    build, _ = PCBuild.objects.get_or_create(user=request.user)
    # Проверка совместимости
    ok, error = check_compatibility(build, product)
    if not ok:
        return JsonResponse({'success': False, 'error': error}, status=400)
    # Удаляем старый компонент этой категории
    PCBuildComponent.objects.filter(build=build, category=product.category).delete()
    PCBuildComponent.objects.create(build=build, product=product, category=product.category)
    return JsonResponse({'success': True})

@require_POST
@login_required
def api_build_remove(request):
    data = json.loads(request.body)
    product_id = data.get('product_id')
    if not product_id:
        return JsonResponse({'success': False, 'error': 'Нет product_id'}, status=400)
    build = get_object_or_404(PCBuild, user=request.user)
    PCBuildComponent.objects.filter(build=build, product_id=product_id).delete()
    return JsonResponse({'success': True})

@require_POST
@login_required
def api_build_save(request):
    data = json.loads(request.body)
    name = data.get('name')
    if not name:
        return JsonResponse({'success': False, 'error': 'Нет имени'}, status=400)
    build = get_object_or_404(PCBuild, user=request.user)
    components = build.components.select_related('product', 'category')
    build_data = [
        {
            'category_id': c.category.id,
            'category_name': c.category.name,
            'product_id': c.product.id,
            'product_name': c.product.name,
            'price': float(c.product.final_price),
            'quantity': c.quantity,
        } for c in components
    ]
    saved = SavedPCBuild.objects.create(user=request.user, name=name, data=build_data)
    return JsonResponse({'success': True, 'build_id': saved.id, 'name': saved.name})

@login_required
def api_builds(request):
    builds = SavedPCBuild.objects.filter(user=request.user).order_by('-created_at')
    result = []
    for b in builds:
        components = b.data
        total_price = sum(item.get('price', 0) * item.get('quantity', 1) for item in components)
        result.append({
            'id': b.id,
            'name': b.name,
            'created_at': b.created_at,
            'components': components,
            'total_price': total_price,
        })
    return JsonResponse({'success': True, 'configurations': result})

@require_POST
@login_required
def api_build_add_to_cart(request):
    from cart.models import CartItem
    data = json.loads(request.body)
    build_id = data.get('build_id')
    if not build_id:
        return JsonResponse({'success': False, 'error': 'Нет build_id'}, status=400)
    build = get_object_or_404(SavedPCBuild, id=build_id, user=request.user)
    for item in build.data:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 1)
        product = get_object_or_404(Product, id=product_id)
        cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()
    return JsonResponse({'success': True})

@require_POST
@login_required
def api_delete_configuration(request, config_id):
    try:
        build = SavedPCBuild.objects.get(id=config_id, user=request.user)
        build.delete()
        return JsonResponse({'success': True})
    except SavedPCBuild.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Конфигурация не найдена'}, status=404)

# --- Вспомогательные функции ---
def compare_values(val1, val2, operator):
    try:
        v1 = float(val1)
        v2 = float(val2)
    except Exception:
        v1 = str(val1)
        v2 = str(val2)
    if operator == '=':
        return v1 == v2
    if operator == '!=':
        return v1 != v2
    if operator == '<':
        return v1 < v2
    if operator == '<=':
        return v1 <= v2
    if operator == '>':
        return v1 > v2
    if operator == '>=':
        return v1 >= v2
    return False

def get_spec_value(product, spec):
    # spec: Specification instance
    ps = ProductSpec.objects.filter(product=product, specification=spec).first()
    return ps.value if ps else None

def check_compatibility(build, new_product):
    rules = CompatibilityRule.objects.all()
    # Получаем все компоненты сборки (category_id -> product)
    components = {c.category_id: c.product for c in build.components.select_related('product', 'category')}
    # Добавляем новый продукт в копию сборки
    components[new_product.category_id] = new_product
    for rule in rules:
        prod1 = components.get(rule.category1_id)
        prod2 = components.get(rule.category2_id)
        if not prod1 or not prod2:
            continue
        val1 = get_spec_value(prod1, rule.spec1)
        val2 = get_spec_value(prod2, rule.spec2)
        if val1 is None or val2 is None:
            continue
        if not compare_values(val1, val2, rule.operator):
            return False, rule.error_message
    return True, ''


from django.template.loader import render_to_string
def computer_catalog(request):
    ...
    # """Основная страница каталога компьютеров"""
    # categories = CategoryPC.objects.all()
    # # По умолчанию показываем компьютеры для игр
    # default_category = categories.filter(name='gaming').first()
    # computers = Computer.objects.filter(category=default_category) if default_category else []
    
    # context = {
    #     'categories': categories,
    #     'computers': computers,
    #     'selected_category': default_category.name if default_category else 'gaming'
    # }
    
    # return render(request, 'catalog/computer_catalog.html', context)

def get_computers_by_category(request, category_name):
    ...
    # """AJAX endpoint для получения компьютеров по категории"""
    # try:
    #     category = CategoryPC.objects.get(name=category_name)
    #     computers = Computer.objects.filter(category=category)
        
    #     # Рендерим только секцию с компьютерами
    #     html = render_to_string('catalog/computers_section.html', {
    #         'computers': computers
    #     })
        
    #     return JsonResponse({
    #         'success': True,
    #         'html': html
    #     })
    # except Category.DoesNotExist:
    #     return JsonResponse({
    #         'success': False,
    #         'error': 'Категория не найдена'
    #     })
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_GET
from store.models import Product

@staff_member_required
@require_GET
def get_products_by_category(request):
    """AJAX view для получения товаров по категории"""
    category_id = request.GET.get('category_id')
    
    if not category_id:
        return JsonResponse({'products': []})
    
    try:
        products = Product.objects.filter(category_id=category_id).values('id', 'name')
        return JsonResponse({'products': list(products)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_POST
def api_load_prebuilt(request):
    """Загрузка готовой конфигурации в конфигуратор пользователя"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Необходимо войти в систему', 'redirect': '/accounts/login/'})
    
    try:
        data = json.loads(request.body)
        prebuilt_id = data.get('prebuilt_id')
        
        if not prebuilt_id:
            return JsonResponse({'success': False, 'error': 'Не указан ID конфигурации'})
        
        # Получаем готовую конфигурацию
        prebuilt = get_object_or_404(PrebuiltPC, id=prebuilt_id)
        
        # Получаем или создаем сборку пользователя
        build, created = PCBuild.objects.get_or_create(user=request.user)
        
        # Очищаем текущую сборку
        PCBuildComponent.objects.filter(build=build).delete()
        
        # Загружаем компоненты из готовой конфигурации
        with transaction.atomic():
            for component in prebuilt.components.all():
                PCBuildComponent.objects.create(
                    build=build,
                    product=component.product,
                    category=component.category,
                    quantity=component.quantity
                )
        
        return JsonResponse({'success': True, 'message': 'Конфигурация успешно загружена'})
        
    except PrebuiltPC.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Конфигурация не найдена'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Ошибка загрузки: {str(e)}'})

def get_products_by_category(request):
    category_id = request.GET.get('category_id')
    if category_id:
        products = Product.objects.filter(category_id=category_id).values('id', 'name')
        return JsonResponse({'products': list(products)})
    return JsonResponse({'products': []})

