from django.core.management.base import BaseCommand
from store.models import ProductLine, Category, Specification, Product, ProductSpec
from django.core.files.base import ContentFile

class Command(BaseCommand):
    help = 'Создаёт тестовые категории, спецификации и товары для конфигуратора ПК.'

    def handle(self, *args, **options):
        # 1. ProductLine
        pl, _ = ProductLine.objects.get_or_create(name='Комплектующие', slug='komplektuyushchie')

        # 2. Категории
        categories = [
            ('Процессор', 'processor'),
            ('Видеокарта', 'videokarta'),
            ('Оперативная память', 'ram'),
            ('Материнская плата', 'motherboard'),
            ('Блок питания', 'psu'),
        ]
        cat_objs = {}
        for name, slug in categories:
            cat, _ = Category.objects.get_or_create(product_line=pl, name=name, slug=slug)
            cat_objs[slug] = cat

        # 3. Спецификации
        specs = {
            'processor': [('Сокет', 'шт'), ('Ядер', 'шт'), ('Потоков', 'шт')],
            'videokarta': [('Объем памяти', 'ГБ'), ('Тип памяти', '')],
            'ram': [('Объем', 'ГБ'), ('Тип', '')],
            'motherboard': [('Сокет', ''), ('Чипсет', '')],
            'psu': [('Мощность', 'Вт')],
        }
        spec_objs = {}
        for cat_slug, spec_list in specs.items():
            cat = cat_objs[cat_slug]
            for spec_name, unit in spec_list:
                spec, _ = Specification.objects.get_or_create(category=cat, name=spec_name, unit=unit)
                spec_objs[(cat_slug, spec_name)] = spec

        # 4. Товары и характеристики
        products = [
            # Процессоры
            ('Intel Core i5-12400F', 'processor', 12000, {'Сокет': 'LGA1700', 'Ядер': '6', 'Потоков': '12'}),
            ('AMD Ryzen 5 5600X', 'processor', 13500, {'Сокет': 'AM4', 'Ядер': '6', 'Потоков': '12'}),
            # Видеокарты
            ('NVIDIA RTX 3060', 'videokarta', 32000, {'Объем памяти': '12', 'Тип памяти': 'GDDR6'}),
            ('AMD Radeon RX 6600', 'videokarta', 27000, {'Объем памяти': '8', 'Тип памяти': 'GDDR6'}),
            # Оперативная память
            ('Kingston Fury 16GB', 'ram', 4500, {'Объем': '16', 'Тип': 'DDR4'}),
            ('Corsair Vengeance 32GB', 'ram', 8500, {'Объем': '32', 'Тип': 'DDR4'}),
            # Материнские платы
            ('ASUS PRIME B660M', 'motherboard', 9000, {'Сокет': 'LGA1700', 'Чипсет': 'B660'}),
            ('MSI B550M PRO', 'motherboard', 9500, {'Сокет': 'AM4', 'Чипсет': 'B550'}),
            # Блоки питания
            ('Chieftec 600W', 'psu', 3500, {'Мощность': '600'}),
            ('Corsair 750W', 'psu', 5200, {'Мощность': '750'}),
        ]
        for name, cat_slug, price, spec_dict in products:
            cat = cat_objs[cat_slug]
            prod, _ = Product.objects.get_or_create(name=name, category=cat, price=price)
            for spec_name, value in spec_dict.items():
                spec = spec_objs[(cat_slug, spec_name)]
                ProductSpec.objects.get_or_create(product=prod, specification=spec, value=value)
        self.stdout.write(self.style.SUCCESS('Тестовые товары и категории успешно созданы!')) 