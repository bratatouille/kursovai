from django.db import models
from django.conf import settings
from store.models import Product, PromoCode

class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart_items', verbose_name='Пользователь')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    quantity = models.PositiveIntegerField('Количество', default=1)
    added_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Корзина'

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def total_price(self):
        """Общая стоимость позиции"""
        return self.product.final_price * self.quantity


class CartPromoCode(models.Model):
    """Примененный промокод в корзине пользователя"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='cart_promocode',
        verbose_name='Пользователь'
    )
    promocode = models.ForeignKey(PromoCode, on_delete=models.CASCADE, verbose_name='Промокод')
    applied_at = models.DateTimeField('Дата применения', auto_now_add=True)

    class Meta:
        verbose_name = 'Промокод в корзине'
        verbose_name_plural = 'Промокоды в корзине'

    def __str__(self):
        return f"{self.user.email} - {self.promocode.code}"