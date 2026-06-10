from django.core.management.base import BaseCommand
from django.db import transaction
from store.models import ProductLine, Category, Specification
from pcbuilder.models import CategoryPC

class Command(BaseCommand):
    help = 'Создает базовые данные для сборки ПК'

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write('Создание базовых данных для сборки ПК...')
            
            # Создаем раздел "Комплектующие"
            components_line, created = ProductLine.objects.get_or_create(
                slug='komplektuyushchie',
                defaults={
                    'name': 'Комплектующие'
                }
            )
            if created:
                self.stdout.write(f'✓ Создан раздел: {components_line.name}')
            else:
                self.stdout.write(f'• Раздел уже существует: {components_line.name}')

            # Создаем категории комплектующих
            categories_data = [
                {
                    'slug': 'processor',
                    'name': 'Процессоры',
                    'specifications': [
                        ('Сокет', ''),
                        ('Количество ядер', 'шт'),
                        ('Количество потоков', 'шт'),
                        ('Базовая частота', 'ГГц'),
                        ('Максимальная частота', 'ГГц'),
                        ('Техпроцесс', 'нм'),
                        ('TDP', 'Вт'),
                        ('Встроенная графика', ''),
                        ('Поддержка памяти', ''),
                        ('Максимальный объем памяти', 'ГБ'),
                    ]
                },
                {
                    'slug': 'motherboard',
                    'name': 'Материнские платы',
                    'specifications': [
                        ('Сокет', ''),
                        ('Чипсет', ''),
                        ('Форм-фактор', ''),
                        ('Поддержка памяти', ''),
                        ('Максимальный объем памяти', 'ГБ'),
                        ('Количество слотов памяти', 'шт'),
                        ('Слоты расширения', ''),
                        ('Встроенная сетевая карта', ''),
                        ('Встроенная звуковая карта', ''),
                        ('USB порты', 'шт'),
                        ('SATA порты', 'шт'),
                        ('M.2 слоты', 'шт'),
                    ]
                },
                {
                    'slug': 'videokarta',
                    'name': 'Видеокарты',
                    'specifications': [
                        ('Графический процессор', ''),
                        ('Объем видеопамяти', 'ГБ'),
                        ('Тип памяти', ''),
                        ('Разрядность шины памяти', 'бит'),
                        ('Базовая частота GPU', 'МГц'),
                        ('Boost частота GPU', 'МГц'),
                        ('Частота памяти', 'МГц'),
                        ('Интерфейс подключения', ''),
                        ('Разъемы питания', ''),
                        ('Рекомендуемая мощность БП', 'Вт'),
                        ('Длина карты', 'мм'),
                        ('Количество вентиляторов', 'шт'),
                        ('Выходы', ''),
                    ]
                },
                {
                    'slug': 'ram',
                    'name': 'Оперативная память',
                    'specifications': [
                        ('Тип памяти', ''),
                        ('Объем модуля', 'ГБ'),
                        ('Количество модулей в комплекте', 'шт'),
                        ('Общий объем', 'ГБ'),
                        ('Частота', 'МГц'),
                        ('Тайминги', ''),
                        ('Напряжение', 'В'),
                        ('Поддержка XMP/DOCP', ''),
                        ('Радиатор', ''),
                        ('RGB подсветка', ''),
                    ]
                },
                {
                    'slug': 'storage',
                    'name': 'Накопители',
                    'specifications': [
                        ('Тип накопителя', ''),
                        ('Объем', 'ГБ'),
                        ('Форм-фактор', ''),
                        ('Интерфейс', ''),
                        ('Скорость чтения', 'МБ/с'),
                        ('Скорость записи', 'МБ/с'),
                        ('Тип памяти', ''),
                        ('Ресурс записи', 'TBW'),
                        ('MTBF', 'часов'),
                    ]
                },
                {
                    'slug': 'psu',
                    'name': 'Блоки питания',
                    'specifications': [
                        ('Мощность', 'Вт'),
                        ('Сертификат 80 PLUS', ''),
                        ('Форм-фактор', ''),
                        ('Модульность', ''),
                        ('Вентилятор', 'мм'),
                        ('Разъемы питания материнской платы', ''),
                        ('Разъемы питания процессора', ''),
                        ('Разъемы питания видеокарт', ''),
                        ('SATA разъемы', 'шт'),
                        ('Molex разъемы', 'шт'),
                        ('Активный PFC', ''),
                        ('Защиты', ''),
                    ]
                },
                {
                    'slug': 'case',
                    'name': 'Корпуса',
                    'specifications': [
                        ('Форм-фактор', ''),
                        ('Материал', ''),
                        ('Цвет', ''),
                        ('Боковая панель', ''),
                        ('Размеры', 'мм'),
                        ('Вес', 'кг'),
                        ('Максимальная длина видеокарты', 'мм'),
                        ('Максимальная высота кулера', 'мм'),
                        ('Места для накопителей 3.5"', 'шт'),
                        ('Места для накопителей 2.5"', 'шт'),
                        ('Предустановленные вентиляторы', 'шт'),
                        ('Места для вентиляторов', 'шт'),
                        ('USB порты', 'шт'),
                        ('Аудио разъемы', 'шт'),
                    ]
                },
                {
                    'slug': 'cooling',
                    'name': 'Системы охлаждения',
                    'specifications': [
                        ('Тип охлаждения', ''),
                        ('Сокеты', ''),
                        ('Размер вентилятора', 'мм'),
                        ('Количество вентиляторов', 'шт'),
                        ('Скорость вращения', 'об/мин'),
                        ('Уровень шума', 'дБ'),
                        ('Воздушный поток', 'CFM'),
                        ('TDP', 'Вт'),
                        ('Высота кулера', 'мм'),
                        ('Материал радиатора', ''),
                        ('Тепловые трубки', 'шт'),
                        ('RGB подсветка', ''),
                        ('Размер радиатора (для СВО)', 'мм'),
                    ]
                }
            ]

            # Создаем категории и их характеристики
            for cat_data in categories_data:
                category, created = Category.objects.get_or_create(
                    product_line=components_line,
                    slug=cat_data['slug'],
                    defaults={
                        'name': cat_data['name']
                    }
                )
                
                if created:
                    self.stdout.write(f'✓ Создана категория: {category.name}')
                else:
                    self.stdout.write(f'• Категория уже существует: {category.name}')

                # Создаем характеристики для категории
                for spec_name, spec_unit in cat_data['specifications']:
                    spec, spec_created = Specification.objects.get_or_create(
                        category=category,
                        name=spec_name,
                        defaults={
                            'unit': spec_unit
                        }
                    )
                    if spec_created:
                        self.stdout.write(f'  ✓ Создана характеристика: {spec_name}')

            # Создаем категории назначения ПК
            pc_categories_data = [
                {
                    'name': 'gaming',
                    'display_name': 'Для игр',
                    'description': 'Мощные игровые компьютеры для современных игр',
                    'icon': 'fas fa-gamepad'
                },
                {
                    'name': 'work',
                    'display_name': 'Для работы',
                    'description': 'Производительные рабочие станции',
                    'icon': 'fas fa-briefcase'
                },
                {
                    'name': 'office',
                    'display_name': 'Для офиса',
                    'description': 'Компактные офисные решения',
                    'icon': 'fas fa-building'
                },
                {
                    'name': 'design',
                    'display_name': 'Для дизайна',
                    'description': 'Специализированные ПК для дизайнеров и художников',
                    'icon': 'fas fa-palette'
                },
                {
                    'name': 'study',
                    'display_name': 'Для учебы',
                    'description': 'Доступные решения для студентов',
                    'icon': 'fas fa-graduation-cap'
                },
                {
                    'name': 'streaming',
                    'display_name': 'Для стриминга',
                    'description': 'Мощные ПК для стриминга и создания контента',
                    'icon': 'fas fa-video'
                }
            ]

            self.stdout.write('\nСоздание категорий назначения ПК...')
            for pc_cat_data in pc_categories_data:
                pc_category, created = CategoryPC.objects.get_or_create(
                    name=pc_cat_data['name'],
                    defaults={
                        'display_name': pc_cat_data['display_name'],
                        'description': pc_cat_data['description'],
                        'icon': pc_cat_data['icon']
                    }
                )
                
                if created:
                    self.stdout.write(f'✓ Создана категория ПК: {pc_category.display_name}')
                else:
                    self.stdout.write(f'• Категория ПК уже существует: {pc_category.display_name}')

            self.stdout.write(
                self.style.SUCCESS('\n✅ Базовые данные для сборки ПК успешно созданы!')
            )
            self.stdout.write(
                'Теперь вы можете добавлять товары в созданные категории через админ-панель.'
            )