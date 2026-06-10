from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('become-seller/', views.become_seller_view, name='become_seller'),
    path('seller/', views.seller_dashboard_view, name='seller_dashboard'),
    path('seller/products/new/', views.seller_product_create_view, name='seller_product_create'),
    path('seller/products/<int:product_id>/edit/', views.seller_product_edit_view, name='seller_product_edit'),
    
    # API endpoints
    path('api/promocodes/', views.get_user_promocodes, name='api_promocodes'),
    path('api/configurations/', views.get_user_configurations, name='api_configurations'),
    path('api/orders/', views.get_user_orders, name='api_orders'),
    path('api/seller/dashboard/', views.get_seller_dashboard, name='api_seller_dashboard'),
    path('api/seller/categories/', views.get_seller_categories, name='api_seller_categories'),
    path('api/seller/specifications/', views.get_category_specs, name='api_seller_specifications'),
    path('api/seller/products/create/', views.create_seller_product, name='api_seller_product_create'),
]
