from django.db import models
from django.conf import settings
from store.models import Product

# Create your models here.

class FavoriteItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_items', verbose_name='Пользователь')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    added_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return self.product.name
