from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import FavoriteItem
from store.models import Product
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

@login_required
def favorites(request):
    favorites = FavoriteItem.objects.filter(user=request.user)
    return render(request, 'favorites/favorites.html', {'favorites': favorites})

@require_POST
@csrf_exempt
@login_required
def add_to_favorites(request):
    product_id = request.POST.get('product_id')
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Товар не найден.'}, status=404)
    favorite, created = FavoriteItem.objects.get_or_create(user=request.user, product=product)
    if created:
        return JsonResponse({'success': True, 'added': True})
    else:
        return JsonResponse({'success': True, 'added': False, 'error': 'Уже в избранном.'})

@require_POST
@csrf_exempt
@login_required
def remove_from_favorites(request):
    product_id = request.POST.get('product_id')
    try:
        favorite = FavoriteItem.objects.get(user=request.user, product_id=product_id)
        favorite.delete()
        return JsonResponse({'success': True})
    except FavoriteItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Товар не найден в избранном.'}, status=404)

@require_POST
@csrf_exempt
@login_required
def toggle_favorite(request, product_slug):
    try:
        product = Product.objects.get(slug=product_slug)
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Товар не найден.'}, status=404)
    favorite, created = FavoriteItem.objects.get_or_create(user=request.user, product=product)
    if created:
        return JsonResponse({'success': True, 'in_wishlist': True})
    else:
        favorite.delete()
        return JsonResponse({'success': True, 'in_wishlist': False})
