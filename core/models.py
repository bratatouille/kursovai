from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

# Create your models here.

class HeroSlide(models.Model):
    """Слайды для главной страницы"""
    title = models.CharField('Заголовок', max_length=200)
    subtitle = models.CharField('Подзаголовок', max_length=300)
    image = models.ImageField('Изображение', upload_to='hero_slides/')
    button1_text = models.CharField('Текст кнопки 1', max_length=50, blank=True)
    button1_url = models.URLField('URL кнопки 1', max_length=200, blank=True)
    button2_text = models.CharField('Текст кнопки 2', max_length=50, blank=True)
    button2_url = models.URLField('URL кнопки 2', max_length=200, blank=True)
    order = models.PositiveIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Слайд'
        verbose_name_plural = 'Слайды'
        ordering = ['order']

    def __str__(self):
        return self.title

class Advantage(models.Model):
    ICON_CHOICES = [
        ('star', 'Звезда'),
        ('shield', 'Щит'),
        ('support', 'Поддержка'),
        ('rocket', 'Ракета'),
        ('gift', 'Подарок'),
        ('heart', 'Сердце'),
    ]
    icon = models.CharField('Иконка', max_length=20, choices=ICON_CHOICES, default='star')
    color = models.CharField('Цвет иконки (hex)', max_length=20, default='#7a85ff')
    title = models.CharField('Заголовок', max_length=100)
    description = models.CharField('Описание', max_length=300)
    order = models.PositiveIntegerField('Порядок', default=0)
    active = models.BooleanField('Активен', default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Преимущество'
        verbose_name_plural = 'Преимущества'

    def __str__(self):
        return self.title

class ContactInfo(models.Model):
    """Контактная информация для сайта"""
    address = models.CharField('Адрес', max_length=255)
    phone = models.CharField('Телефон', max_length=20)
    email = models.EmailField('Email')
    schedule = models.CharField('Режим работы', max_length=100)
    map_link = models.URLField('Ссылка на карту', max_length=500, blank=True)

    class Meta:
        verbose_name = 'Контактная информация'
        verbose_name_plural = 'Контактная информация'

    def __str__(self):
        return "Контактная информация"

class SupportTicket(models.Model):
    """Модель для заявок в поддержку"""
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_progress', 'В обработке'),
        ('closed', 'Закрыта'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Пользователь')
    name = models.CharField('Имя', max_length=100)
    email = models.EmailField('Email')
    topic = models.CharField('Тема', max_length=100)
    message = models.TextField('Сообщение')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Заявка в поддержку'
        verbose_name_plural = 'Заявки в поддержку'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заявка от {self.name} ({self.topic})"
