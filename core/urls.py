from django.urls import path
from .views import index, about, support_view, payments, delivery, computer_catalog, get_computers_by_category, send_promocode_email

app_name = 'core'

urlpatterns = [
    path('', index, name='index'),
    path('about/', about, name='about'),
    path('support/', support_view, name='support'),
    path('payments/', payments, name='payments'),
    path('delivery/', delivery, name='delivery'),
    path('pc/', computer_catalog, name='computer_catalog'),
    path('pc/<str:category_name>/', get_computers_by_category, name='get_computers_by_category'),
    path('send_promocode/', send_promocode_email, name='send_promocode'),
]
