from django.urls import path
from . import views

app_name = 'favorites'

urlpatterns = [
    path('', views.favorites, name='favorites'),
    path('add/', views.add_to_favorites, name='add_to_favorites'),
    path('remove/', views.remove_from_favorites, name='remove_from_favorites'),
    path('toggle/<slug:product_slug>/', views.toggle_favorite, name='toggle_favorite'),
] 