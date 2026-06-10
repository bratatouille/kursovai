from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_GET
from .forms import UserUpdateForm, UserRegisterForm, BecomeSellerForm, SellerProductForm
from store.models import PromoCode, PromoCodeUsage, UserPromoCode
from pcbuilder.models import SavedPCBuild
from order.models import Order
from django.db import models
from django.utils import timezone
from store.models import Product, Category, Specification, ProductSpec, ProductImage
from django.views.decorators.http import require_POST
from django.utils.text import slugify


User = get_user_model()


def _seller_required(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden('Требуется авторизация.')
    if not request.user.is_seller:
        return HttpResponseForbidden('Доступ только для продавцов.')
    return None

def login_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')  # В нашем случае это email
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.email}!')
                return redirect('users:profile')
            else:
                messages.error(request, 'Неверный email или пароль.')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('users:profile')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация успешна!')
            return redirect('users:profile')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы.')
    return redirect('core:index')

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлен!')
            return redirect('users:profile')
    else:
        form = UserUpdateForm(instance=request.user)
    
    return render(request, 'users/profile.html', {
        'form': form,
        'become_seller_form': BecomeSellerForm(instance=request.user),
        'user': request.user
    })


@login_required
def become_seller_view(request):
    if request.method != 'POST':
        return redirect('users:profile')

    if request.user.is_seller:
        messages.info(request, 'Ваш аккаунт уже имеет роль продавца.')
        return redirect('users:profile')

    form = BecomeSellerForm(request.POST, instance=request.user)
    if not form.is_valid():
        messages.error(request, 'Укажите корректное название магазина.')
        return redirect('users:profile')

    user = form.save(commit=False)
    user.is_seller = True
    user.save(update_fields=['seller_name', 'is_seller'])
    messages.success(request, 'Роль продавца успешно подключена.')
    return redirect('users:profile')

@require_GET
@login_required
def get_user_promocodes(request):
    """API для получения промокодов пользователя с улучшенной логикой"""
    try:
        user = request.user
        now = timezone.now()
        
        # Получаем все персональные промокоды пользователя через связующую модель
        personal_promo_ids = UserPromoCode.objects.filter(user=user).values_list('promocode_id', flat=True)
        # Получаем все общие (не персональные и не email) активные промокоды
        public_promos = PromoCode.objects.filter(
            allowed_users__isnull=True,
            is_personal=False,
            is_email=False
        )
        # Получаем объекты персональных промокодов (назначенных этому пользователю)
        personal_promos = PromoCode.objects.filter(id__in=personal_promo_ids, is_personal=True)
        # Объединяем все релевантные промокоды в один запрос, чтобы избежать дублирования
        all_relevant_promos = (public_promos | personal_promos).distinct().prefetch_related('allowed_categories')
        
        # Получаем информацию об использовании промокодов этим пользователем
        user_usages = PromoCodeUsage.objects.filter(user=user).values('promocode_id').annotate(count=models.Count('id'))
        user_usage_map = {usage['promocode_id']: usage['count'] for usage in user_usages}

        promocodes_data = {
            'personal': [],
            'available': [],
            'used': []
        }

        for promo in all_relevant_promos:
            user_usage_count = user_usage_map.get(promo.id, 0)
            is_personal = promo.id in personal_promo_ids
            
            # Определяем статус и категорию
            is_used_by_user = user_usage_count >= promo.usage_limit_per_user
            is_expired = promo.end_date and promo.end_date < now
            is_not_started = promo.start_date and promo.start_date > now
            is_globally_used_up = promo.usage_limit is not None and promo.used_count >= promo.usage_limit
            is_inactive_by_status = promo.status != 'active'

            display_status = 'active'
            target_list = 'available'
            
            if is_used_by_user:
                display_status = 'used'
                target_list = 'used'
            elif is_expired:
                display_status = 'expired'
                target_list = 'used'
            elif is_globally_used_up:
                display_status = 'used_up'
                target_list = 'used'
            elif is_inactive_by_status:
                display_status = promo.status
                target_list = 'used'
            elif is_not_started:
                display_status = 'not_started'
            
            # Собираем данные промокода
            promo_info = {
                'id': promo.id,
                'code': promo.code,
                'name': promo.name,
                'description': promo.description,
                'discount_type': promo.discount_type,
                'discount_value': float(promo.discount_value),
                'min_order_amount': float(promo.min_order_amount) if promo.min_order_amount else 0,
                'max_discount_amount': float(promo.max_discount_amount) if promo.max_discount_amount else None,
                'start_date': promo.start_date.isoformat() if promo.start_date else None,
                'end_date': promo.end_date.isoformat() if promo.end_date else None,
                'usage_limit': promo.usage_limit,
                'used_count': promo.used_count,
                'usage_limit_per_user': promo.usage_limit_per_user,
                'user_usage_count': user_usage_count,
                'allowed_categories': [cat.name for cat in promo.allowed_categories.all()],
                'display_status': display_status,
            }
            
            # Распределяем по категориям
            if target_list == 'used':
                promocodes_data['used'].append(promo_info)
            elif is_personal:
                promocodes_data['personal'].append(promo_info)
            else:
                promocodes_data['available'].append(promo_info)

        return JsonResponse({
            'success': True,
            'promocodes': promocodes_data
        })
        
    except Exception as e:
        # Логирование ошибки может быть полезно
        # import logging
        # logging.error(f"Error in get_user_promocodes: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)

@require_GET
@login_required
def get_user_configurations(request):
    """API для получения конфигураций пользователя"""
    try:
        configurations = SavedPCBuild.objects.filter(
            user=request.user
        ).order_by('-created_at')
        
        configs_data = []
        for config in configurations:
            # Подсчитываем общую стоимость
            total_price = sum(
                item.get('price', 0) * item.get('quantity', 1) 
                for item in config.data
            )
            
            # Получаем основные компоненты
            components_summary = []
            for item in config.data[:4]:  # Показываем первые 4 компонента
                components_summary.append({
                    'category_name': item.get('category_name', ''),
                    'product_name': item.get('product_name', ''),
                    'price': item.get('price', 0),
                    'quantity': item.get('quantity', 1)
                })
            
            configs_data.append({
                'id': config.id,
                'name': config.name,
                'created_at': config.created_at.strftime('%d.%m.%Y %H:%M'),
                'total_price': total_price,
                'components_count': len(config.data),
                'components_summary': components_summary
            })
        
        return JsonResponse({
            'success': True,
            'configurations': configs_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_GET
@login_required
def get_user_orders(request):
    """API для получения заказов пользователя"""
    try:
        orders = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-created_at')
        
        orders_data = []
        for order in orders:
            # Получаем товары заказа
            order_items = []
            for item in order.items.all():
                order_items.append({
                    'product_name': item.product_name,
                    'product_price': float(item.product_price),
                    'quantity': item.quantity,
                    'total_price': float(item.product_price * item.quantity)
                })
            
            # Определяем статус на русском
            status_display = {
                'pending': 'Ожидает обработки',
                'confirmed': 'Подтвержден',
                'processing': 'В обработке',
                'shipped': 'Отправлен',
                'delivered': 'Доставлен',
                'cancelled': 'Отменен'
            }.get(order.status, order.status)
            
            # Определяем цвет статуса
            status_color = {
                'pending': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
                'confirmed': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
                'processing': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
                'shipped': 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-300',
                'delivered': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
                'cancelled': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
            }.get(order.status, 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300')
            
            orders_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'created_at': order.created_at.strftime('%d.%m.%Y %H:%M'),
                'status': order.status,
                'status_display': status_display,
                'status_color': status_color,
                'total_amount': float(order.total_amount),
                'discount_amount': float(order.discount_amount),
                'subtotal': float(order.subtotal),
                'promocode_used': order.promocode_used,
                'payment_method': order.get_payment_method_display(),
                'items_count': order.items.count(),
                'items': order_items,
                'delivery_address': f"{order.delivery_city}, {order.delivery_street}, {order.delivery_house}" + 
                                  (f", кв. {order.delivery_apartment}" if order.delivery_apartment else "")
            })
        
        return JsonResponse({
            'success': True,
            'orders': orders_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@require_GET
@login_required
def get_seller_dashboard(request):
    if not request.user.is_seller:
        return JsonResponse({
            'success': False,
            'error': 'Доступ только для продавцов.',
        }, status=403)

    products = Product.objects.filter(seller=request.user).select_related('category')
    order_items = (
        Order.objects.filter(items__product__seller=request.user)
        .distinct()
        .order_by('-created_at')
        .prefetch_related('items__product')
    )

    recent_orders = []
    for order in order_items[:10]:
        seller_items = [
            item for item in order.items.all()
            if item.product and item.product.seller_id == request.user.id
        ]
        seller_total = sum(float(item.total_price) for item in seller_items)
        recent_orders.append({
            'order_number': order.order_number,
            'status': order.get_status_display(),
            'created_at': order.created_at.strftime('%d.%m.%Y %H:%M'),
            'items_count': len(seller_items),
            'seller_total': seller_total,
        })

    products_data = [{
        'id': product.id,
        'name': product.name,
        'category': product.category.name,
        'price': float(product.price),
        'stock': product.stock,
        'is_in_stock': product.is_in_stock,
        'is_low_stock': product.is_low_stock,
    } for product in products.order_by('-id')[:20]]

    return JsonResponse({
        'success': True,
        'seller': {
            'name': request.user.seller_name or request.user.get_full_name() or request.user.email,
        },
        'stats': {
            'products_count': products.count(),
            'orders_count': order_items.count(),
            'revenue': round(sum(order['seller_total'] for order in recent_orders), 2),
        },
        'products': products_data,
        'recent_orders': recent_orders,
    })


@login_required
def seller_dashboard_view(request):
    if not request.user.is_seller:
        messages.error(request, 'Доступ только для продавцов.')
        return redirect('users:profile')

    products = Product.objects.filter(seller=request.user).select_related('category').order_by('-id')
    return render(request, 'users/seller_dashboard.html', {
        'products': products,
    })


@login_required
def seller_product_create_view(request):
    if not request.user.is_seller:
        messages.error(request, 'Доступ только для продавцов.')
        return redirect('users:profile')

    if request.method == 'POST':
        form = SellerProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user

            base_slug = slugify(product.name)[:180] or 'product'
            slug = base_slug
            counter = 2
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug[:170]}-{counter}"
                counter += 1
            product.slug = slug
            product.save()

            for spec in Specification.objects.filter(category=product.category):
                value = (request.POST.get(f'spec_{spec.id}') or '').strip()
                if value:
                    ProductSpec.objects.create(
                        product=product,
                        specification=spec,
                        value=value,
                    )

            gallery_images = request.FILES.getlist('gallery_images')
            for idx, image in enumerate(gallery_images, start=1):
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    order=idx,
                    is_main=(idx == 1),
                )

            messages.success(request, f'Товар "{product.name}" успешно опубликован.')
            return redirect('users:seller_dashboard')
    else:
        form = SellerProductForm()

    return render(request, 'users/seller_product_form.html', {
        'form': form,
        'product': None,
        'existing_specs': {},
    })


@login_required
def seller_product_edit_view(request, product_id):
    if not request.user.is_seller:
        messages.error(request, 'Доступ только для продавцов.')
        return redirect('users:profile')

    product = Product.objects.filter(id=product_id, seller=request.user).first()
    if not product:
        messages.error(request, 'Товар не найден или недоступен.')
        return redirect('users:seller_dashboard')

    if request.method == 'POST':
        form = SellerProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            updated_product = form.save()

            # Обновляем характеристики под текущую категорию.
            category_specs = Specification.objects.filter(category=updated_product.category)
            valid_spec_ids = set(category_specs.values_list('id', flat=True))

            ProductSpec.objects.filter(product=updated_product).exclude(
                specification_id__in=valid_spec_ids
            ).delete()

            for spec in category_specs:
                value = (request.POST.get(f'spec_{spec.id}') or '').strip()
                if value:
                    ProductSpec.objects.update_or_create(
                        product=updated_product,
                        specification=spec,
                        defaults={'value': value},
                    )
                else:
                    ProductSpec.objects.filter(
                        product=updated_product,
                        specification=spec,
                    ).delete()

            remove_ids = request.POST.getlist('remove_gallery_image_ids')
            if remove_ids:
                ProductImage.objects.filter(
                    product=updated_product,
                    id__in=remove_ids,
                ).delete()

            current_max_order = (
                ProductImage.objects.filter(product=updated_product)
                .aggregate(models.Max('order'))
                .get('order__max') or 0
            )
            gallery_images = request.FILES.getlist('gallery_images')
            for idx, image in enumerate(gallery_images, start=1):
                ProductImage.objects.create(
                    product=updated_product,
                    image=image,
                    order=current_max_order + idx,
                    is_main=False,
                )

            messages.success(request, f'Товар "{updated_product.name}" обновлен.')
            return redirect('users:seller_dashboard')
    else:
        form = SellerProductForm(instance=product)

    existing_specs = {
        item.specification_id: item.value
        for item in ProductSpec.objects.filter(product=product).select_related('specification')
    }
    existing_gallery = ProductImage.objects.filter(product=product).order_by('order', 'id')
    return render(request, 'users/seller_product_form.html', {
        'form': form,
        'product': product,
        'existing_specs': existing_specs,
        'existing_gallery': existing_gallery,
    })


@require_POST
@login_required
def create_seller_product(request):
    if not request.user.is_seller:
        return JsonResponse({
            'success': False,
            'error': 'Доступ только для продавцов.',
        }, status=403)

    name = (request.POST.get('name') or '').strip()
    category_id = request.POST.get('category_id')
    description = (request.POST.get('description') or '').strip()

    try:
        price = float(request.POST.get('price', '0'))
        stock = int(request.POST.get('stock', '0'))
        discount = int(request.POST.get('discount', '0'))
    except (TypeError, ValueError):
        return JsonResponse({
            'success': False,
            'error': 'Некорректные числовые значения.',
        }, status=400)

    if not name:
        return JsonResponse({'success': False, 'error': 'Название товара обязательно.'}, status=400)
    if price <= 0:
        return JsonResponse({'success': False, 'error': 'Цена должна быть больше 0.'}, status=400)
    if stock < 0:
        return JsonResponse({'success': False, 'error': 'Остаток не может быть отрицательным.'}, status=400)
    if not 0 <= discount <= 99:
        return JsonResponse({'success': False, 'error': 'Скидка должна быть в диапазоне 0-99.'}, status=400)

    try:
        category = Category.objects.get(pk=category_id)
    except (Category.DoesNotExist, ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Категория не найдена.'}, status=400)

    base_slug = slugify(name)[:180] or 'product'
    slug = base_slug
    counter = 2
    while Product.objects.filter(slug=slug).exists():
        slug = f"{base_slug[:170]}-{counter}"
        counter += 1

    product = Product.objects.create(
        seller=request.user,
        category=category,
        name=name,
        slug=slug,
        price=price,
        stock=stock,
        discount=discount,
        description=description,
    )

    return JsonResponse({
        'success': True,
        'product': {
            'id': product.id,
            'name': product.name,
        },
    })


@require_GET
@login_required
def get_seller_categories(request):
    if not request.user.is_seller:
        return JsonResponse({
            'success': False,
            'error': 'Доступ только для продавцов.',
        }, status=403)

    categories = Category.objects.select_related('product_line').order_by('product_line__name', 'name')
    return JsonResponse({
        'success': True,
        'categories': [
            {
                'id': category.id,
                'name': category.name,
                'product_line': category.product_line.name,
            }
            for category in categories
        ],
    })


@require_GET
@login_required
def get_category_specs(request):
    forbidden = _seller_required(request)
    if forbidden:
        return forbidden

    category_id = request.GET.get('category_id')
    try:
        category = Category.objects.get(pk=category_id)
    except (Category.DoesNotExist, TypeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Категория не найдена.'}, status=404)

    specs = Specification.objects.filter(category=category).order_by('name')
    return JsonResponse({
        'success': True,
        'specifications': [
            {
                'id': spec.id,
                'name': spec.name,
                'unit': spec.unit,
            } for spec in specs
        ]
    })