from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction
from cart.models import CartItem, CartPromoCode
from store.models import PromoCode, PromoCodeUsage
from .models import Order, OrderItem, OrderStatusHistory
from decimal import Decimal

@login_required
def checkout(request):
    """Страница оформления заказа"""
    # Получаем товары из корзины
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    
    if not cart_items.exists():
        messages.error(request, 'Ваша корзина пуста')
        return redirect('cart:cart')
    
    # Рассчитываем суммы
    subtotal = sum(item.product.final_price * item.quantity for item in cart_items)
    
    # Проверяем промокод
    applied_promocode = None
    discount_amount = Decimal('0')
    
    try:
        cart_promocode = CartPromoCode.objects.get(user=request.user)
        promocode = cart_promocode.promocode
        
        # Проверяем валидность промокода
        is_valid, error_message = promocode.is_valid(user=request.user, order_amount=subtotal)
        
        if is_valid:
            applied_promocode = promocode
            discount_amount = promocode.calculate_discount(subtotal)
        else:
            # Если промокод стал невалидным, удаляем его
            cart_promocode.delete()
            messages.warning(request, f'Промокод "{promocode.code}" больше не действителен: {error_message}')
            
    except CartPromoCode.DoesNotExist:
        pass
    
    total_amount = subtotal - discount_amount
    
    # Предзаполняем форму данными пользователя
    user_data = {
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'email': request.user.email,
        'phone': getattr(request.user, 'phone', ''),
        'delivery_region': getattr(request.user, 'delivery_region', ''),
        'delivery_city': getattr(request.user, 'delivery_city', ''),
        'delivery_street': getattr(request.user, 'delivery_street', ''),
        'delivery_house': getattr(request.user, 'delivery_house', ''),
        'delivery_apartment': getattr(request.user, 'delivery_apartment', ''),
        'delivery_postal_code': getattr(request.user, 'delivery_postal_code', ''),
    }
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'discount_amount': discount_amount,
        'total_amount': total_amount,
        'applied_promocode': applied_promocode,
        'user_data': user_data,
    }
    
    return render(request, 'order/checkout.html', context)

@require_POST
@login_required
def create_order(request):
    """Создание заказа"""
    try:
        with transaction.atomic():
            # Получаем товары из корзины
            cart_items = CartItem.objects.filter(user=request.user).select_related('product')
            
            if not cart_items.exists():
                return JsonResponse({'success': False, 'error': 'Корзина пуста'})
            
            # Рассчитываем суммы
            subtotal = sum(item.product.final_price * item.quantity for item in cart_items)
            discount_amount = Decimal('0')
            promocode_code = ''
            applied_promocode = None
            
            # Проверяем промокод
            try:
                cart_promocode = CartPromoCode.objects.get(user=request.user)
                promocode = cart_promocode.promocode
                
                # Еще раз проверяем валидность промокода перед созданием заказа
                is_valid, error_message = promocode.is_valid(user=request.user, order_amount=subtotal)
                
                if is_valid:
                    applied_promocode = promocode
                    discount_amount = promocode.calculate_discount(subtotal)
                    promocode_code = promocode.code
                else:
                    # Если промокод стал невалидным, удаляем его и возвращаем ошибку
                    cart_promocode.delete()
                    return JsonResponse({
                        'success': False, 
                        'error': f'Промокод "{promocode.code}" больше не действителен: {error_message}'
                    })
                    
            except CartPromoCode.DoesNotExist:
                pass
            
            total_amount = subtotal - discount_amount
            
            # Создаем заказ
            order = Order.objects.create(
                user=request.user,
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                email=request.POST.get('email'),
                phone=request.POST.get('phone'),
                delivery_region=request.POST.get('delivery_region'),
                delivery_city=request.POST.get('delivery_city'),
                delivery_street=request.POST.get('delivery_street'),
                delivery_house=request.POST.get('delivery_house'),
                delivery_apartment=request.POST.get('delivery_apartment', ''),
                delivery_postal_code=request.POST.get('delivery_postal_code', ''),
                subtotal=subtotal,
                discount_amount=discount_amount,
                total_amount=total_amount,
                payment_method=request.POST.get('payment_method', 'cash'),
                comment=request.POST.get('comment', ''),
                promocode_used=promocode_code,
            )
            
            # Создаем товары заказа
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    product_name=cart_item.product.name,
                    product_price=cart_item.product.final_price,
                    quantity=cart_item.quantity,
                )
                
                # Уменьшаем количество товара на складе
                if hasattr(cart_item.product, 'stock'):
                    cart_item.product.stock = max(0, cart_item.product.stock - cart_item.quantity)
                    cart_item.product.save()
            
            # Записываем использование промокода
            if applied_promocode:
                # Создаем запись об использовании промокода
                PromoCodeUsage.objects.create(
                    promocode=applied_promocode,
                    user=request.user,
                    order_id=order.id,
                    discount_amount=discount_amount,
                    order_amount=subtotal
                )
                
                # Увеличиваем счетчик использований промокода
                applied_promocode.used_count += 1
                applied_promocode.save()
                
                # Проверяем, не исчерпан ли промокод
                if applied_promocode.usage_limit and applied_promocode.used_count >= applied_promocode.usage_limit:
                    applied_promocode.status = 'used_up'
                    applied_promocode.save()
            
            # Создаем запись в истории статусов
            OrderStatusHistory.objects.create(
                order=order,
                status='pending',
                comment='Заказ создан',
                created_by=request.user
            )
            
            # Очищаем корзину и промокод
            cart_items.delete()
            CartPromoCode.objects.filter(user=request.user).delete()
            
            return JsonResponse({
                'success': True, 
                'order_id': order.id,
                'order_number': order.order_number,
                'redirect_url': f'/orders/{order.id}/',
                'message': f'Заказ #{order.order_number} успешно создан' + 
                          (f' со скидкой {discount_amount} ₽' if discount_amount > 0 else '')
            })
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка создания заказа для пользователя {request.user.email}: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Произошла ошибка при создании заказа'})

@login_required
def order_detail(request, order_id):
    """Детали заказа"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.select_related('product')
    status_history = order.status_history.all()
    
    # Получаем информацию об использованном промокоде
    promocode_usage = None
    if order.promocode_used:
        try:
            promocode_usage = PromoCodeUsage.objects.get(
                user=request.user,
                order_id=order.id
            )
        except PromoCodeUsage.DoesNotExist:
            pass
    
    context = {
        'order': order,
        'order_items': order_items,
        'status_history': status_history,
        'promocode_usage': promocode_usage,
    }
    
    return render(request, 'order/order_detail.html', context)

@require_POST
@login_required
def cancel_order(request, order_id):
    """Отмена заказа пользователем, если статус позволяет"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status not in ['pending', 'processing']:
        return JsonResponse({'success': False, 'error': 'Заказ уже нельзя отменить.'}, status=400)
    order.status = 'cancelled'
    order.save()
    OrderStatusHistory.objects.create(
        order=order,
        status='cancelled',
        comment='Заказ отменён пользователем',
        created_by=request.user
    )
    return JsonResponse({'success': True, 'message': 'Заказ успешно отменён.'})
