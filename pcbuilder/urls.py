from django.urls import path
from . import views

app_name = 'pcbuilder'

urlpatterns = [
    path('', views.configurator, name='pcbuilder'),

    path('api/categories/', views.api_categories, name='api_categories'),
    path('api/category-filters/', views.api_category_filters, name='api_category_filters'),
    path('api/products/', views.api_products, name='api_products'),
    path('api/build/', views.api_build, name='api_build'),
    path('api/build/add/', views.api_build_add, name='api_build_add'),
    path('api/build/remove/', views.api_build_remove, name='api_build_remove'),
    path('api/build/save/', views.api_build_save, name='api_build_save'),
    path('api/builds/', views.api_builds, name='api_builds'),
    path('api/build/add_to_cart/', views.api_build_add_to_cart, name='api_build_add_to_cart'),
    path('api/delete-configuration/<int:config_id>/', views.api_delete_configuration, name='api_delete_configuration'),
    path('api/load-prebuilt/', views.api_load_prebuilt, name='api_load_prebuilt'),
]

# URL для админки
admin_urlpatterns = [
    path('get-products-by-category/', views.get_products_by_category, name='get_products_by_category_admin'),
]

urlpatterns += admin_urlpatterns
