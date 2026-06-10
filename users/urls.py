from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # API endpoints
    path('api/promocodes/', views.get_user_promocodes, name='api_promocodes'),
    path('api/configurations/', views.get_user_configurations, name='api_configurations'),
    path('api/orders/', views.get_user_orders, name='api_orders'),
]
