from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .forms import UserUpdateForm, UserRegisterForm
from store.models import PromoCode, PromoCodeUsage, UserPromoCode
from pcbuilder.models import SavedPCBuild
from order.models import Order
from django.db import models
from django.utils import timezone


User = get_user_model()

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
        'user': request.user
    })

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