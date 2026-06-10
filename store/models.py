from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from decimal import Decimal
from django.core.exceptions import ValidationError

# Create your models here.

class ProductLine(models.Model):
    """Разделы товаров (Комплектующие, Периферия)"""
    name = models.CharField('Название', max_length=100, unique=True)
    slug = models.SlugField('URL', max_length=100, unique=True)
    image = models.ImageField('Изображение', upload_to='product_lines/', blank=True, null=True)

    class Meta:
        verbose_name = 'Раздел'
        verbose_name_plural = 'Разделы'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Category(models.Model):
    """Категории (Процессоры, Видеокарты)"""
    product_line = models.ForeignKey(
        ProductLine,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name='Раздел'
    )
    name = models.CharField('Название', max_length=100)
    slug = models.SlugField('URL', max_length=100, unique=True)
    image = models.ImageField('Изображение', upload_to='categories/', blank=True, null=True)

    PROTECTED_SLUGS = [
        'videokarta', 'processor', 'motherboard', 'storage',
        'case', 'ram', 'cooling', 'psu'
    ]

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        unique_together = ('product_line', 'name')

    def __str__(self):
        return f"{self.product_line.name} → {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        
        if self.pk:
            orig = Category.objects.get(pk=self.pk)
            # Запрещаем менять name и slug для системных категорий
            if orig.slug in self.PROTECTED_SLUGS:
                if orig.name != self.name or orig.slug != self.slug:
                    raise ValidationError(
                        "Изменение имени или URL для системных категорий, "
                        "используемых в конфигураторе ПК, запрещено!"
                    )
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.slug in self.PROTECTED_SLUGS:
            raise ValidationError("Удаление системных категорий, используемых в конфигураторе ПК, запрещено!")
        super().delete(*args, **kwargs)

class Specification(models.Model):
    """Характеристики категории"""
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='specifications',
    )
    name = models.CharField('Название', max_length=100)
    unit = models.CharField('Единица измерения', max_length=20, blank=True)

    class Meta:
        verbose_name = 'Характеристика'
        verbose_name_plural = 'Характеристики'
        unique_together = ('category', 'name')

    def __str__(self):
        return f"{self.category.name} - {self.name}"

class Product(models.Model):
    """Товары"""
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='Категория'
    )
    name = models.CharField('Название', max_length=200)
    slug = models.SlugField('URL', max_length=200, unique=True)
    price = models.DecimalField(
        'Цена',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    discount = models.PositiveIntegerField('Скидка (%)', default=0)
    # Добавляем поле для количества на складе
    stock = models.PositiveIntegerField(
        'Количество на складе', 
        default=0,
        help_text='Количество товара на складе'
    )
    # Добавляем поле для минимального остатка (опционально)
    min_stock = models.PositiveIntegerField(
        'Минимальный остаток',
        default=0,
        help_text='Минимальное количество для предупреждения о заканчивающемся товаре'
    )
    is_popular = models.BooleanField(
        'Популярный товар',
        default=False,
        help_text='Отметьте, если товар является популярным и должен отображаться в специальных блоках.'
    )
    description = models.TextField(
        'Описание',
        blank=True,
        default='',
        help_text='Можно использовать HTML-теги для форматирования текста (например, <ul>, <li>, <b>, <h3> и т.д.)'
    )
    image = models.ImageField('Фото', upload_to='products/', blank=True, null=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def secondary_image(self):
        """Возвращает первое изображение из галереи для превью на карточке."""
        return self.images.order_by('order').first()

    @property
    def final_price(self):
        if self.discount:
            discount_decimal = Decimal(str(self.discount)) / Decimal('100')
            return self.price * (Decimal('1') - discount_decimal)
        return self.price

    def formatted_price(self):
        """Форматированная цена с разделителями"""
        return f"{int(self.final_price):,}".replace(',', ' ') + ' ₽'

    @property
    def is_in_stock(self):
        """Проверка наличия товара на складе"""
        return self.stock > 0

    @property
    def is_low_stock(self):
        """Проверка на низкий остаток"""
        return 0 < self.stock <= self.min_stock

    def can_order(self, quantity=1):
        """Проверка возможности заказа определенного количества"""
        return self.stock >= quantity

class ProductImage(models.Model):
    """Галерея изображений для товара"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name='Товар')
    image = models.ImageField('Изображение', upload_to='products/gallery/')
    alt_text = models.CharField('Описание изображения', max_length=255, blank=True, default='')
    order = models.PositiveIntegerField('Порядок', default=0, help_text='Для сортировки изображений')
    is_main = models.BooleanField('Основное изображение', default=False, help_text='Показывать как главное')

    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Галерея изображений'
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.product.name} — {self.alt_text or self.image.name}"

class ProductSpec(models.Model):
    """Значения характеристик для товаров"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specs', verbose_name='Товар')
    specification = models.ForeignKey(Specification, on_delete=models.CASCADE, verbose_name='Характеристика')
    value = models.CharField('Значение', max_length=100)

    class Meta:
        verbose_name = 'Характеристика товара'
        verbose_name_plural = 'Характеристики товаров'
        unique_together = ('product', 'specification')

    def __str__(self):
        return f"{self.product.name}: {self.specification.name} = {self.value}"

from django.contrib.auth import get_user_model
from django.utils import timezone
import string
import random

User = get_user_model()

class PromoCode(models.Model):
    """Промокоды"""
    DISCOUNT_TYPE_CHOICES = [
        ('percent', 'Процент'),
        ('fixed', 'Фиксированная сумма'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Активный'),
        ('inactive', 'Неактивный'),
        ('expired', 'Истек'),
        ('used_up', 'Исчерпан'),
    ]

    code = models.CharField('Код промокода', max_length=50, unique=True)
    name = models.CharField('Название', max_length=100, help_text='Внутреннее название для администратора')
    description = models.TextField('Описание', blank=True, help_text='Описание акции')
    
    # Тип и размер скидки
    discount_type = models.CharField('Тип скидки', max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='percent')
    discount_value = models.DecimalField('Размер скидки', max_digits=10, decimal_places=2)
    
    # Ограничения по сумме заказа
    min_order_amount = models.DecimalField(
        'Минимальная сумма заказа', 
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text='Минимальная сумма заказа для применения промокода'
    )
    max_discount_amount = models.DecimalField(
        'Максимальная сумма скидки',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Максимальная сумма скидки (только для процентных скидок)'
    )
    
    # Ограничения по времени
    start_date = models.DateTimeField('Дата начала действия')
    end_date = models.DateTimeField('Дата окончания действия')
    
    # Ограничения по использованию
    usage_limit = models.PositiveIntegerField(
        'Лимит использований', 
        null=True, 
        blank=True,
        help_text='Общее количество использований промокода (оставьте пустым для неограниченного)'
    )
    usage_limit_per_user = models.PositiveIntegerField(
        'Лимит на пользователя',
        default=1,
        help_text='Сколько раз один пользователь может использовать промокод'
    )
    used_count = models.PositiveIntegerField('Количество использований', default=0)
    
    # Привязка к пользователям
    allowed_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='allowed_promocodes',
        help_text='Пользователи, которые могут использовать этот промокод (оставьте пустым для всех)'
    )
    
    # Привязка к категориям товаров (опционально)
    allowed_categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='promocodes',
        help_text='Категории товаров, к которым применяется промокод (оставьте пустым для всех)'
    )
    
    status = models.CharField('Статус', max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    is_personal = models.BooleanField('Персональный', default=False, help_text='Если выбран, промокод не показывается никому, пока не назначен пользователям')
    is_email = models.BooleanField('Email', default=False, help_text='Если выбран, промокод не показывается никому, но может быть использован для рассылки')

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} ({self.name})"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_code(length=8):
        """Генерация случайного промокода"""
        characters = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choice(characters) for _ in range(length))
            if not PromoCode.objects.filter(code=code).exists():
                return code

    def is_valid(self, user=None, order_amount=None):
        """Проверка валидности промокода"""
        from django.utils import timezone
        
        now = timezone.now()
        
        # Проверка статуса
        if self.status != 'active':
            return False, 'Промокод неактивен'
        
        # Проверка времени действия
        if now < self.start_date:
            return False, 'Промокод еще не активен'
        
        if now > self.end_date:
            return False, 'Промокод истек'
        
        # Проверка лимита использований
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False, 'Промокод исчерпан'
        
        # Проверка минимальной суммы заказа
        if order_amount and order_amount < self.min_order_amount:
            return False, f'Минимальная сумма заказа: {self.min_order_amount} ₽'
        
        # Проверка пользователя
        if user and user.is_authenticated:
            # Проверка разрешенных пользователей (если есть ограничения)
            allowed_users = self.allowed_users.all()
            if allowed_users.exists() and user not in allowed_users:
                return False, 'Промокод недоступен для вашего аккаунта'
            
            # Проверка лимита на пользователя
            user_usage_count = PromoCodeUsage.objects.filter(
                promocode=self, 
                user=user
            ).count()
            
            print(f"DEBUG: Промокод {self.code}, пользователь {user.email}")
            print(f"DEBUG: Использований пользователем: {user_usage_count}")
            print(f"DEBUG: Лимит на пользователя: {self.usage_limit_per_user}")
            
            if user_usage_count >= self.usage_limit_per_user:
                return False, f'Вы уже использовали этот промокод максимальное количество раз ({self.usage_limit_per_user})'
    
        return True, 'Промокод действителен'

    def calculate_discount(self, order_amount):
        """Расчет размера скидки"""
        if self.discount_type == 'percent':
            discount = order_amount * (self.discount_value / 100)
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
        else:  # фикс
            discount = self.discount_value
        
        # Скидка не может быть больше суммы заказа
        return min(discount, order_amount)


class PromoCodeUsage(models.Model):
    """История использования промокодов"""
    promocode = models.ForeignKey(PromoCode, on_delete=models.CASCADE, related_name='usages', verbose_name='Промокод')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='promocode_usages', verbose_name='Пользователь')
    order_id = models.PositiveIntegerField('ID заказа', null=True, blank=True)  # Связь с заказом
    discount_amount = models.DecimalField('Размер скидки', max_digits=10, decimal_places=2)
    order_amount = models.DecimalField('Сумма заказа', max_digits=10, decimal_places=2)
    used_at = models.DateTimeField('Дата использования', auto_now_add=True)

    class Meta:
        verbose_name = 'Использование промокода'
        verbose_name_plural = 'История использования промокодов'
        ordering = ['-used_at']

    def __str__(self):
        return f"{self.user.email} использовал {self.promocode.code}"


class UserPromoCode(models.Model):
    """Персональные промокоды пользователей"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personal_promocodes', verbose_name='Пользователь')
    promocode = models.ForeignKey(PromoCode, on_delete=models.CASCADE, verbose_name='Промокод')
    assigned_at = models.DateTimeField('Дата назначения', auto_now_add=True)
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_promocodes',
        help_text='Кто назначил промокод',
        verbose_name='Кто назначает'
    )
    is_notified = models.BooleanField('Уведомлен', default=False)

    class Meta:
        verbose_name = 'Персональный промокод'
        verbose_name_plural = 'Персональные промокоды'
        unique_together = ('user', 'promocode')

    def __str__(self):
        return f"{self.user.email} - {self.promocode.code}"