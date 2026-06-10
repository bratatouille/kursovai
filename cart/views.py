from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import CartItem, CartPromoCode
from store.models import Product, PromoCode
from decimal import Decimal
import json

@login_required
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    
    # Подсчет сумм
    order_sum = sum(item.product.price * item.quantity for item in cart_items)
    total_sum = sum(item.product.final_price * item.quantity for item in cart_items)
    
    # Проверяем примененный промокод
    applied_promocode = None
    discount_amount = Decimal('0')
    final_total = total_sum
    
    try:
        cart_promocode = CartPromoCode.objects.get(user=request.user)
        promocode = cart_promocode.promocode
        
        # Проверяем валидность промокода при каждом обращении к корзине
        is_valid, error_message = promocode.is_valid(user=request.user, order_amount=total_sum)
        
        if is_valid:
            applied_promocode = promocode
            discount_amount = promocode.calculate_discount(total_sum)
            final_total = total_sum - discount_amount
        else:
            # Если промокод стал невалидным, удаляем его
            cart_promocode.delete()
            # Можно добавить сообщение пользователю
            from django.contrib import messages
            messages.warning(request, f'Промокод "{promocode.code}" больше не действителен: {error_message}')
            
    except CartPromoCode.DoesNotExist:
        pass
    
    context = {
        'cart_items': cart_items,
        'order_sum': order_sum,
        'total_sum': total_sum,
        'applied_promocode': applied_promocode,
        'discount_amount': discount_amount,
        'final_total': final_total,
    }
    
    # Если это AJAX запрос, возвращаем только HTML
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'cart/cart.html', context)
    
    return render(request, 'cart/cart.html', context)

    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    
    # Подсчет сумм
    order_sum = sum(item.product.price * item.quantity for item in cart_items)
    total_sum = sum(item.product.final_price * item.quantity for item in cart_items)
    
    # Проверяем примененный промокод
    applied_promocode = None
    discount_amount = Decimal('0')
    final_total = total_sum
    
    try:
        cart_promocode = CartPromoCode.objects.get(user=request.user)
        promocode = cart_promocode.promocode
        
        # Проверяем валидность промокода
        is_valid, error_message = promocode.is_valid(user=request.user, order_amount=total_sum)
        
        if is_valid:
            applied_promocode = promocode
            discount_amount = promocode.calculate_discount(total_sum)
            final_total = total_sum - discount_amount
        else:
            # Если промокод стал невалидным, удаляем его
            cart_promocode.delete()
            
    except CartPromoCode.DoesNotExist:
        pass
    
    context = {
        'cart_items': cart_items,
        'order_sum': order_sum,
        'total_sum': total_sum,
        'applied_promocode': applied_promocode,
        'discount_amount': discount_amount,
        'final_total': final_total,
    }
    
    # Если это AJAX запрос, возвращаем только HTML
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'cart/cart.html', context)
    
    return render(request, 'cart/cart.html', context)

@require_POST
@csrf_exempt
@login_required
def add_to_cart(request):
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Товар не найден.'}, status=404)
    
    # Получаем stock из модели Product
    max_qty = product.stock if hasattr(product, 'stock') and product.stock > 0 else 99
    
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        new_quantity = cart_item.quantity + quantity
        if new_quantity > max_qty:
            cart_item.quantity = max_qty
        else:
            cart_item.quantity = new_quantity
        cart_item.save()
    else:
        cart_item.quantity = min(quantity, max_qty)
        cart_item.save()
    
    return JsonResponse({
        'success': True, 
        'quantity': cart_item.quantity, 
        'max_qty': max_qty
    })
@require_POST
@csrf_exempt
@login_required
def remove_from_cart(request):
    """Уменьшение количества товара на 1"""
    product_id = request.POST.get('product_id')
    try:
        cart_item = CartItem.objects.get(user=request.user, product_id=product_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            return JsonResponse({'success': True, 'quantity': cart_item.quantity})
        else:
            cart_item.delete()
            return JsonResponse({'success': True, 'removed': True})
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Товар не найден в корзине.'}, status=404)

@require_POST
@csrf_exempt
@login_required
def delete_from_cart(request):
    """Полное удаление товара из корзины"""
    product_id = request.POST.get('product_id')
    try:
        cart_item = CartItem.objects.get(user=request.user, product_id=product_id)
        cart_item.delete()
        return JsonResponse({'success': True, 'removed': True})
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Товар не найден в корзине.'}, status=404)

@require_POST
@csrf_exempt
@login_required
def add_to_cart_by_slug(request, product_slug):
    try:
        product = Product.objects.get(slug=product_slug)
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Товар не найден.'}, status=404)
    
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    else:
        cart_item.quantity = 1
        cart_item.save()
    
    return JsonResponse({'success': True, 'in_cart': True, 'quantity': cart_item.quantity})

@require_POST
@csrf_exempt
@login_required
def remove_from_cart_by_slug(request, product_slug):
    try:
        cart_item = CartItem.objects.get(user=request.user, product__slug=product_slug)
        cart_item.delete()
        return JsonResponse({'success': True, 'in_cart': False})
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Товар не найден в корзине.'}, status=404)

@require_POST
@csrf_exempt
@login_required
def apply_promocode(request):
    try:
        data = json.loads(request.body)
        promocode_text = data.get('promocode', '').strip().upper()
        
        if not promocode_text:
            return JsonResponse({
                'success': False, 
                'error': 'Введите промокод'
            })
        
        # Ищем промокод
        try:
            promocode = PromoCode.objects.get(code=promocode_text)
        except PromoCode.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': 'Промокод не найден'
            })
        
        # Получаем сумму корзины
        cart_items = CartItem.objects.filter(user=request.user)
        if not cart_items.exists():
            return JsonResponse({
                'success': False, 
                'error': 'Корзина пуста'
            })
        
        total_sum = sum(item.product.final_price * item.quantity for item in cart_items)
        
        # Проверяем валидность промокода
        is_valid, error_message = promocode.is_valid(
            user=request.user, 
            order_amount=total_sum
        )
        
        if not is_valid:
            return JsonResponse({
                'success': False, 
                'error': error_message
            })
        
        # Проверяем категории (если указаны)
        if promocode.allowed_categories.exists():
            cart_categories = set(item.product.category for item in cart_items)
            allowed_categories = set(promocode.allowed_categories.all())
            
            if not cart_categories.intersection(allowed_categories):
                return JsonResponse({
                    'success': False, 
                    'error': 'Промокод не применим к товарам в корзине'
                })
        
        # Удаляем старый промокод если есть
        CartPromoCode.objects.filter(user=request.user).delete()
        
        # Применяем новый промокод
        CartPromoCode.objects.create(user=request.user, promocode=promocode)
        
        # Рассчитываем скидку
        discount_amount = promocode.calculate_discount(total_sum)
        final_total = total_sum - discount_amount
        
        return JsonResponse({
            'success': True,
            'promocode': {
                'code': promocode.code,
                'name': promocode.name,
                'discount_amount': float(discount_amount),
                'total_sum': float(total_sum),
                'final_total': float(final_total),
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'error': 'Неверный формат данных'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': 'Произошла ошибка при применении промокода'
        })

@require_POST
@csrf_exempt
@login_required
def remove_promocode(request):
    try:
        CartPromoCode.objects.filter(user=request.user).delete()
        
        # Пересчитываем суммы
        cart_items = CartItem.objects.filter(user=request.user)
        total_sum = sum(item.product.final_price * item.quantity for item in cart_items)
        
        return JsonResponse({
            'success': True,
            'total_sum': float(total_sum),
            'final_total': float(total_sum),
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': 'Произошла ошибка при удалении промокода'
        })
