from django.core.management.base import BaseCommand
from django.db import transaction
from store.models import ProductLine, Category, Product, ProductSpec, Specification
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Создает тестовые товары для сборки ПК'

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write('Создание тестовых товаров...')
            
            # Получаем категории
            try:
                processor_cat = Category.objects.get(slug='processor')
                motherboard_cat = Category.objects.get(slug='motherboard')
                videokarta_cat = Category.objects.get(slug='videokarta')
                ram_cat = Category.objects.get(slug='ram')
                storage_cat = Category.objects.get(slug='storage')
                psu_cat = Category.objects.get(slug='psu')
                case_cat = Category.objects.get(slug='case')
                cooling_cat = Category.objects.get(slug='cooling')
            except Category.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR('Сначала выполните команду: python manage.py create_pc_data')
                )
                return

            # Тестовые процессоры
            processors_data = [
                {
                    'name': 'Intel Core i5-12400F',
                    'price': Decimal('15990'),
                    'discount': 5,
                    'specs': {
                        'Сокет': 'LGA1700',
                        'Количество ядер': '6',
                        'Количество потоков': '12',
                        'Базовая частота': '2.5',
                        'Максимальная частота': '4.4',
                        'Техпроцесс': '10',
                        'TDP': '65',
                        'Встроенная графика': 'Нет',
                        'Поддержка памяти': 'DDR4-3200, DDR5-4800',
                        'Максимальный объем памяти': '128',
                    }
                },
                {
                    'name': 'AMD Ryzen 5 5600X',
                    'price': Decimal('14990'),
                    'discount': 10,
                    'specs': {
                        'Сокет': 'AM4',
                        'Количество ядер': '6',
                        'Количество потоков': '12',
                        'Базовая частота': '3.7',
                        'Максимальная частота': '4.6',
                        'Техпроцесс': '7',
                        'TDP': '65',
                        'Встроенная графика': 'Нет',
                        'Поддержка памяти': 'DDR4-3200',
                        'Максимальный объем памяти': '128',
                    }
                },
                {
                    'name': 'Intel Core i7-12700K',
                    'price': Decimal('28990'),
                    'discount': 0,
                    'specs': {
                        'Сокет': 'LGA1700',
                        'Количество ядер': '12',
                        'Количество потоков': '20',
                        'Базовая частота': '3.6',
                        'Максимальная частота': '5.0',
                        'Техпроцесс': '10',
                        'TDP': '125',
                        'Встроенная графика': 'Intel UHD Graphics 770',
                        'Поддержка памяти': 'DDR4-3200, DDR5-4800',
                        'Максимальный объем памяти': '128',
                    }
                }
            ]

            # Материнские платы
            motherboards_data = [
                {
                    'name': 'ASUS PRIME B660M-A',
                    'price': Decimal('8990'),
                    'discount': 0,
                    'specs': {
                        'Сокет': 'LGA1700',
                        'Чипсет': 'Intel B660',
                        'Форм-фактор': 'mATX',
                        'Поддержка памяти': 'DDR4',
                        'Максимальный объем памяти': '128',
                        'Количество слотов памяти': '4',
                        'Слоты расширения': '1x PCIe 4.0 x16, 1x PCIe 3.0 x16',
                        'Встроенная сетевая карта': '1 Гбит/с',
                        'Встроенная звуковая карта': '7.1',
                        'USB порты': '8',
                        'SATA порты': '4',
                        'M.2 слоты': '2',
                    }
                },
                {
                    'name': 'MSI B450 TOMAHAWK MAX',
                    'price': Decimal('7490'),
                    'discount': 15,
                    'specs': {
                        'Сокет': 'AM4',
                        'Чипсет': 'AMD B450',
                        'Форм-фактор': 'ATX',
                        'Поддержка памяти': 'DDR4',
                        'Максимальный объем памяти': '128',
                        'Количество слотов памяти': '4',
                        'Слоты расширения': '1x PCIe 3.0 x16, 1x PCIe 2.0 x16',
                        'Встроенная сетевая карта': '1 Гбит/с',
                        'Встроенная звуковая карта': '7.1',
                        'USB порты': '6',
                        'SATA порты': '6',
                        'M.2 слоты': '2',
                    }
                }
            ]

            # Видеокарты
            videocards_data = [
                {
                    'name': 'NVIDIA GeForce RTX 4060',
                    'price': Decimal('32990'),
                    'discount': 5,
                    'specs': {
                        'Графический процессор': 'NVIDIA GeForce RTX 4060',
                        'Объем видеопамяти': '8',
                        'Тип памяти': 'GDDR6',
                        'Разрядность шины памяти': '128',
                        'Базовая частота GPU': '1830',
                        'Boost частота GPU': '2460',
                        'Частота памяти': '17000',
                        'Интерфейс подключения': 'PCIe 4.0 x16',
                        'Разъемы питания': '1x 8-pin',
                        'Рекомендуемая мощность БП': '550',
                        'Длина карты': '244',
                        'Количество вентиляторов': '2',
                        'Выходы': '1x HDMI 2.1, 3x DisplayPort 1.4a',
                    }
                },
                {
                    'name': 'AMD Radeon RX 6600 XT',
                    'price': Decimal('24990'),
                    'discount': 20,
                    'specs': {
                        'Графический процессор': 'AMD Radeon RX 6600 XT',
                        'Объем видеопамяти': '8',
                        'Тип памяти': 'GDDR6',
                        'Разрядность шины памяти': '128',
                        'Базовая частота GPU': '1968',
                        'Boost частота GPU': '2589',
                        'Частота памяти': '16000',
                        'Интерфейс подключения': 'PCIe 4.0 x8',
                        'Разъемы питания': '1x 8-pin',
                        'Рекомендуемая мощность БП': '500',
                        'Длина карты': '267',
                        'Количество вентиляторов': '2',
                        'Выходы': '1x HDMI 2.1, 3x DisplayPort 1.4',
                    }
                },
                {
                    'name': 'NVIDIA GeForce RTX 4070 Ti',
                    'price': Decimal('64990'),
                    'discount': 0,
                    'specs': {
                        'Графический процессор': 'NVIDIA GeForce RTX 4070 Ti',
                        'Объем видеопамяти': '12',
                        'Тип памяти': 'GDDR6X',
                        'Разрядность шины памяти': '192',
                        'Базовая частота GPU': '2310',
                        'Boost частота GPU': '2610',
                        'Частота памяти': '21000',
                        'Интерфейс подключения': 'PCIe 4.0 x16',
                        'Разъемы питания': '1x 16-pin',
                        'Рекомендуемая мощность БП': '700',
                        'Длина карты': '304',
                        'Количество вентиляторов': '3',
                        'Выходы': '1x HDMI 2.1, 3x DisplayPort 1.4a',
                    }
                }
            ]

            # Оперативная память
            ram_data = [
                {
                    'name': 'Corsair Vengeance LPX 16GB (2x8GB) DDR4-3200',
                    'price': Decimal('4990'),
                    'discount': 10,
                    'specs': {
                        'Тип памяти': 'DDR4',
                        'Объем модуля': '8',
                        'Количество модулей в комплекте': '2',
                        'Общий объем': '16',
                        'Частота': '3200',
                        'Тайминги': '16-18-18-36',
                        'Напряжение': '1.35',
                        'Поддержка XMP/DOCP': 'XMP 2.0',
                        'Радиатор': 'Да',
                        'RGB подсветка': 'Нет',
                    }
                },
                {
                    'name': 'G.Skill Trident Z RGB 32GB (2x16GB) DDR4-3600',
                    'price': Decimal('12990'),
                    'discount': 5,
                    'specs': {
                        'Тип памяти': 'DDR4',
                        'Объем модуля': '16',
                        'Количество модулей в комплекте': '2',
                        'Общий объем': '32',
                        'Частота': '3600',
                        'Тайминги': '16-16-16-36',
                        'Напряжение': '1.35',
                        'Поддержка XMP/DOCP': 'XMP 2.0',
                        'Радиатор': 'Да',
                        'RGB подсветка': 'Да',
                    }
                }
            ]

            # Накопители
            storage_data = [
                {
                    'name': 'Samsung 980 NVMe SSD 1TB',
                    'price': Decimal('6990'),
                    'discount': 15,
                    'specs': {
                        'Тип накопителя': 'SSD',
                        'Объем': '1000',
                        'Форм-фактор': 'M.2 2280',
                        'Интерфейс': 'PCIe 3.0 x4',
                        'Скорость чтения': '3500',
                        'Скорость записи': '3000',
                        'Тип памяти': '3D V-NAND',
                        'Ресурс записи': '600',
                        'MTBF': '1500000',
                    }
                },
                {
                    'name': 'Western Digital Blue 2TB HDD',
                    'price': Decimal('4990'),
                    'discount': 0,
                    'specs': {
                        'Тип накопителя': 'HDD',
                        'Объем': '2000',
                        'Форм-фактор': '3.5"',
                        'Интерфейс': 'SATA 6 Гбит/с',
                        'Скорость чтения': '150',
                        'Скорость записи': '150',
                        'Тип памяти': 'CMR',
                        'Ресурс записи': '-',
                        'MTBF': '1000000',
                    }
                }
            ]

            # Блоки питания
            psu_data = [
                {
                    'name': 'Corsair CV650 650W 80+ Bronze',
                    'price': Decimal('5990'),
                    'discount': 0,
                    'specs': {
                        'Мощность': '650',
                        'Сертификат 80 PLUS': 'Bronze',
                        'Форм-фактор': 'ATX',
                        'Модульность': 'Немодульный',
                        'Вентилятор': '120',
                        'Разъемы питания материнской платы': '1x 24-pin',
                        'Разъемы питания процессора': '1x 4+4-pin',
                        'Разъемы питания видеокарт': '2x 6+2-pin',
                        'SATA разъемы': '6',
                        'Molex разъемы': '3',
                        'Активный PFC': 'Да',
                        'Защиты': 'OVP, UVP, OCP, OTP, SCP',
                    }
                },
                {
                    'name': 'Seasonic Focus GX-750 750W 80+ Gold',
                    'price': Decimal('11990'),
                    'discount': 10,
                    'specs': {
                        'Мощность': '750',
                        'Сертификат 80 PLUS': 'Gold',
                        'Форм-фактор': 'ATX',
                        'Модульность': 'Полумодульный',
                        'Вентилятор': '120',
                        'Разъемы питания материнской платы': '1x 24-pin',
                        'Разъемы питания процессора': '2x 4+4-pin',
                        'Разъемы питания видеокарт': '4x 6+2-pin',
                        'SATA разъемы': '8',
                        'Molex разъемы': '4',
                        'Активный PFC': 'Да',
                        'Защиты': 'OVP, UVP, OCP, OTP, SCP, OPP',
                    }
                }
            ]

            # Корпуса
            case_data = [
                {
                    'name': 'Fractal Design Core 1000',
                    'price': Decimal('3990'),
                    'discount': 0,
                    'specs': {
                        'Форм-фактор': 'mATX',
                        'Материал': 'Сталь',
                        'Цвет': 'Черный',
                        'Боковая панель': 'Глухая',
                        'Размеры': '380x175x420',
                        'Вес': '4.5',
                        'Максимальная длина видеокарты': '350',
                        'Максимальная высота кулера': '160',
                        'Места для накопителей 3.5"': '2',
                        'Места для накопителей 2.5"': '3',
                        'Предустановленные вентиляторы': '1',
                        'Места для вентиляторов': '4',
                        'USB порты': '2',
                        'Аудио разъемы': '2',
                    }
                },
                {
                    'name': 'NZXT H510 Elite',
                    'price': Decimal('12990'),
                    'discount': 15,
                    'specs': {
                        'Форм-фактор': 'ATX',
                        'Материал': 'Сталь, закаленное стекло',
                        'Цвет': 'Черный/Белый',
                        'Боковая панель': 'Закаленное стекло',
                        'Размеры': '435x210x460',
                        'Вес': '6.8',
                        'Максимальная длина видеокарты': '381',
                        'Максимальная высота кулера': '165',
                        'Места для накопителей 3.5"': '2',
                        'Места для накопителей 2.5"': '4',
                        'Предустановленные вентиляторы': '4',
                        'Места для вентиляторов': '7',
                        'USB порты': '4',
                        'Аудио разъемы': '2',
                    }
                }
            ]

            # Системы охлаждения
            cooling_data = [
                {
                    'name': 'Cooler Master Hyper 212 Black Edition',
                    'price': Decimal('2990'),
                    'discount': 5,
                    'specs': {
                        'Тип охлаждения': 'Воздушное',
                        'Сокеты': 'LGA1700, LGA1200, AM4, AM5',
                        'Размер вентилятора': '120',
                        'Количество вентиляторов': '1',
                        'Скорость вращения': '650-2000',
                        'Уровень шума': '26',
                        'Воздушный поток': '57.3',
                        'TDP': '150',
                        'Высота кулера': '158.8',
                        'Материал радиатора': 'Алюминий',
                        'Тепловые трубки': '4',
                        'RGB подсветка': 'Нет',
                        'Размер радиатора (для СВО)': '-',
                    }
                },
                {
                    'name': 'Corsair iCUE H100i RGB PRO XT',
                    'price': Decimal('11990'),
                    'discount': 10,
                    'specs': {
                        'Тип охлаждения': 'Жидкостное',
                        'Сокеты': 'LGA1700, LGA1200, AM4, AM5',
                        'Размер вентилятора': '120',
                        'Количество вентиляторов': '2',
                        'Скорость вращения': '400-2400',
                        'Уровень шума': '37',
                        'Воздушный поток': '75',
                        'TDP': '250',
                        'Высота кулера': '27',
                        'Материал радиатора': 'Алюминий',
                        'Тепловые трубки': '-',
                        'RGB подсветка': 'Да',
                        'Размер радиатора (для СВО)': '240',
                    }
                }
            ]

            # Функция для создания товаров
            def create_products(category, products_data):
                for product_data in products_data:
                    # Создаем товар
                    product, created = Product.objects.get_or_create(
                        name=product_data['name'],
                        defaults={
                            'category': category,
                            'price': product_data['price'],
                            'discount': product_data['discount'],
                            'description': f'Высококачественный {category.name.lower()} для сборки ПК.'
                        }
                    )
                    
                    if created:
                        self.stdout.write(f'✓ Создан товар: {product.name}')
                        
                        # Добавляем характеристики
                        for spec_name, spec_value in product_data['specs'].items():
                            try:
                                specification = Specification.objects.get(
                                    category=category,
                                    name=spec_name
                                )
                                ProductSpec.objects.create(
                                    product=product,
                                    specification=specification,
                                    value=spec_value
                                )
                            except Specification.DoesNotExist:
                                self.stdout.write(
                                    self.style.WARNING(f'  Характеристика "{spec_name}" не найдена для категории {category.name}')
                                )
                    else:
                        self.stdout.write(f'• Товар уже существует: {product.name}')

            # Создаем все товары
            create_products(processor_cat, processors_data)
            create_products(motherboard_cat, motherboards_data)
            create_products(videokarta_cat, videocards_data)
            create_products(ram_cat, ram_data)
            create_products(storage_cat, storage_data)
            create_products(psu_cat, psu_data)
            create_products(case_cat, case_data)
            create_products(cooling_cat, cooling_data)

            self.stdout.write(
                self.style.SUCCESS('\n✅ Тестовые товары успешно созданы!')
            )
            
            # Выводим статистику
            total_products = Product.objects.count()
            self.stdout.write(f'Всего товаров в базе: {total_products}')
            
            for category in [processor_cat, motherboard_cat, videokarta_cat, ram_cat, 
                           storage_cat, psu_cat, case_cat, cooling_cat]:
                count = category.products.count()
                self.stdout.write(f'• {category.name}: {count} товаров')
