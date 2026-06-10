from django.urls import path
from .views import catalog, category_detail, product_detail, product_line_detail, search_results, search_ajax

app_name = 'store'

urlpatterns = [
    path('', catalog, name='catalog'),
    path('search/', search_results, name='search'),
    path('api/search/', search_ajax, name='api_search'),
    path('<slug:product_line_slug>/', product_line_detail, name='product_line_detail'),
    path('<slug:product_line_slug>/<slug:category_slug>/', category_detail, name='category_detail'),
    path('<slug:product_line_slug>/<slug:category_slug>/<slug:product_slug>/', product_detail, name='product_detail'),
]
