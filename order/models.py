from django.db import models
from django.conf import settings
from store.models import Product
from decimal import Decimal

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает обработки'),
        ('confirmed', 'Подтвержден'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Наличными при получении'),
        ('card', 'Банковской картой'),
        ('online', 'Онлайн оплата'),
    ]
    
    # Основная информация
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField('Номер заказа', max_length=20, unique=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Контактная информация
    first_name = models.CharField('Имя', max_length=100)
    last_name = models.CharField('Фамилия', max_length=100)
    email = models.EmailField('Email')
    phone = models.CharField('Телефон', max_length=20)
    
    # Адрес доставки
    delivery_region = models.CharField('Регион', max_length=100)
    delivery_city = models.CharField('Город', max_length=100)
    delivery_street = models.CharField('Улица', max_length=200)
    delivery_house = models.CharField('Дом', max_length=20)
    delivery_apartment = models.CharField('Квартира', max_length=20, blank=True)
    delivery_postal_code = models.CharField('Почтовый индекс', max_length=20, blank=True)
    
    # Финансовая информация
    subtotal = models.DecimalField('Сумма товаров', max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField('Размер скидки', max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField('Итоговая сумма', max_digits=10, decimal_places=2)
    
    # Способ оплаты и доставки
    payment_method = models.CharField('Способ оплаты', max_length=20, choices=PAYMENT_METHOD_CHOICES)
    
    # Дополнительная информация
    comment = models.TextField('Комментарий к заказу', blank=True)
    promocode_used = models.CharField('Использованный промокод', max_length=50, blank=True)
    
    # Временные метки
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Заказ #{self.order_number} от {self.user.email}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """Генерация номера заказа"""
        import random
        import string
        from django.utils import timezone
        
        # Формат: YYYYMMDD-XXXX (где XXXX - случайные цифры)
        date_part = timezone.now().strftime('%Y%m%d')
        random_part = ''.join(random.choices(string.digits, k=4))
        order_number = f"{date_part}-{random_part}"
        
        # Проверяем уникальность
        while Order.objects.filter(order_number=order_number).exists():
            random_part = ''.join(random.choices(string.digits, k=4))
            order_number = f"{date_part}-{random_part}"
        
        return order_number
    
    @property
    def full_address(self):
        """Полный адрес доставки"""
        address_parts = [
            self.delivery_region,
            self.delivery_city,
            self.delivery_street,
            f"д. {self.delivery_house}",
        ]
        if self.delivery_apartment:
            address_parts.append(f"кв. {self.delivery_apartment}")
        if self.delivery_postal_code:
            address_parts.append(f"({self.delivery_postal_code})")
        
        return ", ".join(address_parts)


class OrderItem(models.Model):
    """Товары в заказе"""
    order = models.ForeignKey(Order, verbose_name='Заказ', on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, verbose_name='Товар', on_delete=models.CASCADE)
    product_name = models.CharField('Название товара', max_length=200)  # На случай если товар удалят
    product_price = models.DecimalField('Цена за единицу', max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField('Количество')
    total_price = models.DecimalField('Общая стоимость', max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = 'Товар в заказе'
        verbose_name_plural = 'Товары в заказе'
    
    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        # Автоматически рассчитываем общую стоимость
        self.total_price = self.product_price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    """История изменения статусов заказа"""
    order = models.ForeignKey(Order, verbose_name='Заказ', on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField('Статус', max_length=20, choices=Order.STATUS_CHOICES)
    comment = models.TextField('Комментарий', blank=True)
    created_at = models.DateTimeField('Дата изменения', auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Изменил'
    )
    
    class Meta:
        verbose_name = 'История статуса заказа'
        verbose_name_plural = 'История статусов заказов'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Заказ #{self.order.order_number} - {self.get_status_display()}"
