from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('add/', views.add_to_cart, name='add_to_cart'),
    path('remove/', views.remove_from_cart, name='remove_from_cart'),
    path('delete/', views.delete_from_cart, name='delete_from_cart'),  # Новый endpoint для полного удаления
    path('add/<slug:product_slug>/', views.add_to_cart_by_slug, name='add_to_cart_by_slug'),
    path('remove/<slug:product_slug>/', views.remove_from_cart_by_slug, name='remove_from_cart_by_slug'),
    path('apply-promocode/', views.apply_promocode, name='apply_promocode'),
    path('remove-promocode/', views.remove_promocode, name='remove_promocode'),
    path('', views.cart, name='cart'),
]