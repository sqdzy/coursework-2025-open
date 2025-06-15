import random
from decimal import Decimal
from django.db.models import OuterRef, Subquery, DecimalField, Case, When, F
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.contrib.auth import get_user_model, authenticate
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from .serializers import LoginOrRegisterSerializer, CartItemSerializer, OrderSerializer, OrderCreateSerializer, \
    DeliveryMethodSerializer, PaymentMethodSerializer, BannerSerializer, CategorySerializer, CategoryDetailSerializer, \
    ReviewSerializer
from django.utils import timezone
from datetime import timedelta
from faker import Faker
from rest_framework import status, mixins
from django.db import IntegrityError, transaction
from . import serializers

from .models import (
    User, Category, Brand, Feature, OrderStatus, PaymentMethod,
    DeliveryMethod, Product, ProductImage, ProductFeatureValue,
    Order, OrderItem, Banner, BannerTarget, Promotion, PromotionalProduct,
    Review, CartItem, ReviewImage
)
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Prefetch, Q
from .models import Product, ProductImage, Category, Brand, ProductFeatureValue
from .serializers import ProductSerializer, ProductListSerializer
from .utils import annotate_product_prices


def get_realistic_feature_value(feature_name, fake):
    name_lower = feature_name.lower()
    if 'подсветка' in name_lower:
        return random.choice(['RGB', 'Одноцветная (красная)', 'Нет', 'Настраиваемая RGB', 'Белая'])
    if 'тип подключения' in name_lower:
        return random.choice(
            ['Проводное USB', 'Беспроводное 2.4GHz', 'Bluetooth 5.0', 'Проводное + Bluetooth', 'USB Type-C'])
    if 'тип сенсора' in name_lower:
        return random.choice(['Оптический', 'Лазерный', 'Оптический PixArt PMW3360', 'Оптический HERO 25K'])
    if 'dpi' in name_lower or 'разрешение сенсора' in name_lower:
        return f'{random.choice([800, 1600, 3200, 6400, 12000, 16000, 25000])} DPI'
    if 'тип переключателей' in name_lower:
        return random.choice(['Механические (Cherry MX Red)', 'Мембранные', 'Оптико-механические (Razer)', 'Ножничные',
                              'Механические (Gateron Blue)'])
    if 'частота опроса' in name_lower:
        return f'{random.choice([125, 250, 500, 1000, 4000, 8000])} Гц'
    if 'материал' in name_lower and 'амбушюр' not in name_lower:
        return random.choice(['Пластик ABS', 'Алюминий', 'Ткань', 'Металл + Пластик', 'PBT пластик'])
    if 'цвет' in name_lower:
        return fake.color_name()
    if 'вес' in name_lower:
        return f'{random.randint(50, 350)} г'
    if 'размер' in name_lower:
        return random.choice(['Компактный', 'Стандартный', 'Полноразмерный', 'XL', 'M'])
    if 'тип амбушюр' in name_lower:
        return random.choice(['Тканевые', 'Кожзам', 'Велюровые', 'Гибридные', 'Охлаждающий гель'])
    if 'микрофон' in name_lower:
        return random.choice(['Съемный', 'Встроенный', 'Несъемный, откидной', 'Нет'])
    if 'диагональ' in name_lower:
        return f'{random.choice([24, 27, 32, 34])}"'
    if 'разрешение' in name_lower and 'сенсора' not in name_lower:
        return random.choice(['1920x1080 (Full HD)', '2560x1440 (QHD)', '3440x1440 (UWQHD)', '3840x2160 (4K UHD)'])
    if 'частота обновления' in name_lower:
        return f'{random.choice([60, 75, 144, 165, 240, 360])} Гц'
    if 'время отклика' in name_lower:
        return f'{random.choice([1, 2, 4, 5])} мс'
    if 'тип матрицы' in name_lower:
        return random.choice(['IPS', 'VA', 'TN', 'OLED'])
    if 'совместимость' in name_lower:
        return random.choice(['PC', 'PC, MacOS', 'PC, PS5, Xbox Series S/X', 'PC, PS4/5', 'PC, MacOS, Linux'])

    return fake.word() if random.random() > 0.5 else str(random.randint(1, 500))


def faker_view(request):
    fake = Faker("ru_RU")

    USER_COUNT = 15

    BRAND_COUNT = 15
    FEATURE_COUNT = 35
    PRODUCT_COUNT = 60
    ORDER_COUNT = 30
    REVIEW_COUNT = PRODUCT_COUNT * 4
    BANNER_COUNT = 15
    PROMOTION_COUNT = 12

    print("Starting data deletion...")

    Review.objects.all().delete()
    PromotionalProduct.objects.all().delete()
    Promotion.objects.all().delete()
    BannerTarget.objects.all().delete()
    Banner.objects.all().delete()
    OrderItem.objects.all().delete()
    Order.objects.all().delete()
    ProductImage.objects.all().delete()
    ProductFeatureValue.objects.all().delete()
    Product.objects.all().delete()
    Category.objects.all().delete()
    Brand.objects.all().delete()
    Feature.objects.all().delete()
    OrderStatus.objects.all().delete()
    PaymentMethod.objects.all().delete()
    DeliveryMethod.objects.all().delete()
    User.objects.exclude(is_superuser=True).delete()
    print("Data deletion complete.")

    print(f"Creating {USER_COUNT} users...")
    users = [
        User.objects.create_user(
            username=fake.user_name() + str(i),
            email=fake.email(),
            password="password",
            first_name=fake.first_name(),
            last_name=fake.last_name(),
        ) for i in range(USER_COUNT)
    ]

    if not User.objects.filter(is_superuser=True).exists():
        try:
            User.objects.create_superuser('admin', 'admin@example.com', 'password')
            print("Superuser 'admin' created.")
        except IntegrityError:
            print("Superuser 'admin' already exists.")

    print("Users created.")

    print("Creating categories...")
    category_names = ['Мыши', 'Клавиатуры', 'Гарнитуры', 'Коврики для мыши', 'Мониторы', 'Геймпады', 'Веб-камеры',
                      'Микрофоны', 'Кресла', 'Аксессуары (кабели, подставки)']
    categories = []
    for name in category_names:
        desc = f"Все для категории '{name}'. {fake.text(max_nb_chars=100)}"
        cat, created = Category.objects.get_or_create(name=name, defaults={'description': desc})
        categories.append(cat)
    print("Categories created/retrieved.")

    print(f"Creating {BRAND_COUNT} brands...")
    brand_names = ['Razer', 'Logitech G', 'SteelSeries', 'HyperX', 'Corsair', 'ASUS ROG', 'Zowie', 'Glorious',
                   'Cooler Master', 'GamePro', 'Xtrfy', 'Ducky', 'Varmilo', 'Dark Project', 'A4Tech Bloody', 'BenQ',
                   'Samsung', 'LG', 'MSI', 'Canyon', 'Defender']
    needed_brands = BRAND_COUNT - len(brand_names)
    for _ in range(needed_brands): brand_names.append(fake.company() + " Gaming")

    brands = []
    for name in brand_names[:BRAND_COUNT]:
        desc = f"Игровая периферия от {name}. {fake.text(max_nb_chars=120)}"
        brand, created = Brand.objects.get_or_create(name=name, defaults={'description': desc})
        brands.append(brand)
    print("Brands created/retrieved.")

    print(f"Creating {FEATURE_COUNT} features...")
    feature_names = [
        'Тип сенсора', 'Модель сенсора', 'Разрешение сенсора (DPI)', 'Макс. ускорение (G)', 'Частота опроса',
        'Подсветка', 'Тип подключения', 'Количество кнопок', 'Тип переключателей', 'Модель переключателей',
        'Ресурс нажатий клавиш (млн)', 'Материал корпуса', 'Материал клавиш (кейкапов)', 'Цвет', 'Вес', 'Размер',
        'Длина кабеля (м)', 'Тип кабеля', 'Тип амбушюр', 'Материал амбушюр', 'Диаметр динамиков (мм)',
        'Частотный диапазон (наушники)', 'Чувствительность (наушники)', 'Импеданс (Ом)',
        'Микрофон', 'Тип микрофона', 'Частотный диапазон (микрофон)', 'Чувствительность (микрофон)',
        'Шумоподавление микрофона',
        'Диагональ экрана (дюйм)', 'Разрешение экрана', 'Тип матрицы', 'Частота обновления (Гц)',
        'Время отклика (мс, GtG)', 'Яркость (кд/м²)', 'Контрастность', 'Покрытие экрана', 'Интерфейсы',
        'Поддержка HDR', 'Технологии синхронизации', 'Конструкция', 'Совместимость (платформы)',
        'Гарантия (мес)', 'Страна производитель'
    ]
    needed_features = FEATURE_COUNT - len(feature_names)
    for i in range(needed_features): feature_names.append(f"Доп. {fake.word().capitalize()} {i + 1}")

    features = []
    for name in feature_names[:FEATURE_COUNT]:
        feat, created = Feature.objects.get_or_create(name=name)
        features.append(feat)
    print("Features created/retrieved.")

    print("Creating order statuses, payment and delivery methods...")
    order_statuses_data = [("Новый", "Заказ только что создан."), ("Подтвержден", "Заказ подтвержден менеджером."),
                           ("В обработке", "Заказ обрабатывается."),
                           ("Комплектуется", "Товары для заказа собираются на складе."),
                           ("Передан в доставку", "Заказ передан в службу доставки."),
                           ("В пути", "Заказ в пути к клиенту."),
                           ("Ожидает получения", "Заказ прибыл в пункт выдачи или ожидает курьера."),
                           ("Доставлен", "Заказ получен клиентом."), ("Отменен", "Заказ отменен.")]
    order_statuses = [OrderStatus.objects.get_or_create(status=s, defaults={'description': d})[0] for s, d in
                      order_statuses_data]

    payment_methods_data = [("Онлайн картой", "Оплата картой Visa/Mastercard/Мир на сайте."),
                            ("Наличными при получении", "Оплата наличными курьеру или в пункте выдачи."),
                            ("Картой при получении", "Оплата картой курьеру или в пункте выдачи."),
                            ("СБП", "Оплата через Систему Быстрых Платежей."),
                            ("Банковский перевод", "Оплата по счету для юридических лиц.")]
    payment_methods = [PaymentMethod.objects.get_or_create(method_name=m, defaults={'description': d})[0] for m, d in
                       payment_methods_data]

    delivery_methods_data = [
        ("Курьерская доставка (Москва)", "Доставка курьером по Москве до двери в течение 1-2 дней."),
        ("Самовывоз (Москва, Шоурум)", "Забрать заказ из нашего шоурума в Москве."),
        ("Доставка по РФ (СДЭК)", "Доставка ТК СДЭК до пункта выдачи или до двери (3-7 дней)."),
        ("Доставка по РФ (Boxberry)", "Доставка до пункта выдачи Boxberry (4-8 дней)."),
        ("Почта России", "Доставка Почтой России (5-14 дней).")]
    delivery_methods = [DeliveryMethod.objects.get_or_create(method_name=m, defaults={'description': d})[0] for m, d in
                        delivery_methods_data]
    print("Order statuses, payment and delivery methods created/retrieved.")

    print(f"Creating {PRODUCT_COUNT} products...")
    products = []
    product_models = ['Blade', 'Viper', 'DeathAdder', 'Basilisk', 'Naga', 'G Pro', 'G502', 'Apex', 'Arctis', 'Sensei',
                      'Rival', 'Aerox', 'Cloud', 'Alloy', 'Pulsefire', 'Kain', 'Vulcan', 'Strix', 'TUF', 'Model O',
                      'Model D', 'MM710', 'SK622', 'CK550', 'One 3', 'Mecha', 'GPX', 'Phantom', 'Spectre', 'Strike',
                      'Attack', 'Defy', 'Ronin']
    product_suffixes = ['X', 'Pro', 'Elite', 'Mini', 'V2', 'V3', 'Ultimate', 'Wireless', 'TE', 'RGB', 'SE', 'Core',
                        'Air', 'TKL', 'SF', 'HyperSpeed']

    for i in range(PRODUCT_COUNT):
        category = random.choice(categories)
        brand = random.choice(brands)
        model_base = random.choice(product_models)
        suffix = random.choice(product_suffixes) if random.random() > 0.3 else ''
        stock_quantity = random.choice([0, 0, 5, 10, 10, 15, 20, 50, 100])
        year_suffix = f' ({random.randint(2021, 2024)})' if random.random() < 0.15 else ''
        product_name = f"{brand.name} {model_base} {suffix}{year_suffix}".strip().replace('  ', ' ')

        price = Decimal('0.00')
        cat_name = category.name.lower()

        if 'коврик' in cat_name:
            price = round(Decimal(random.uniform(500.0, 4500.0)), 2)
        elif 'аксессуар' in cat_name:
            price = round(Decimal(random.uniform(300.0, 5000.0)), 2)
        elif 'мышь' in cat_name:
            price = round(Decimal(random.uniform(1200.0, 15000.0)), 2)
        elif 'геймпад' in cat_name:
            price = round(Decimal(random.uniform(2000.0, 9000.0)), 2)
        elif 'веб-камер' in cat_name:
            price = round(Decimal(random.uniform(2500.0, 12000.0)), 2)
        elif 'микрофон' in cat_name:
            price = round(Decimal(random.uniform(3000.0, 25000.0)), 2)
        elif 'гарнитур' in cat_name:
            price = round(Decimal(random.uniform(2500.0, 28000.0)), 2)
        elif 'клавиатур' in cat_name:
            price = round(Decimal(random.uniform(3000.0, 30000.0)), 2)
        elif 'кресл' in cat_name:
            price = round(Decimal(random.uniform(15000.0, 50000.0)), 2)
        elif 'монитор' in cat_name:
            price = round(Decimal(random.uniform(12000.0, 120000.0)), 2)
        else:
            price = round(Decimal(random.uniform(1000.0, 10000.0)), 2)

        price = (price // 10) * 10 - Decimal(random.choice([0, 10])) if random.random() > 0.3 else round(
            price / 100) * 100

        product = Product.objects.create(
            name=product_name,
            price=price,
            category=category,
            brand=brand,
            stock=stock_quantity
        )
        products.append(product)
    print("Products created.")

    print("Creating product images...")
    for product in products:
        num_images = random.randint(2, 5)
        has_main = False
        for i in range(num_images):
            is_main = (i == 0 and random.random() > 0.05)
            if is_main: has_main = True
            ProductImage.objects.create(product=product, image=None, main_image=is_main)
        if num_images > 0 and not has_main:
            img = ProductImage.objects.filter(product=product).first()
            if img: img.main_image = True; img.save()
    print("Product images created.")

    print("Creating product features...")
    feature_creation_errors = 0
    for product in products:
        num_features_to_add = random.randint(5, 12)
        available_features = features[:]
        random.shuffle(available_features)
        used_features_count = 0
        product_features = set()
        for feature in available_features:
            if used_features_count >= num_features_to_add: break
            if feature.id in product_features: continue

            cat_name_lower = product.category.name.lower()
            feat_name_lower = feature.name.lower()

            relevant = True
            if (
                    'экран' in feat_name_lower or 'матриц' in feat_name_lower or 'диагонал' in feat_name_lower or 'яркост' in feat_name_lower or 'контраст' in feat_name_lower or 'отклика' in feat_name_lower or 'hdr' in feat_name_lower or 'синхронизац' in feat_name_lower) and 'монитор' not in cat_name_lower: relevant = False
            if (
                    'амбушюр' in feat_name_lower or 'динамик' in feat_name_lower or 'импеданс' in feat_name_lower or 'микрофон' in feat_name_lower or 'чувствительность (наушники)' in feat_name_lower) and (
                    'гарнитур' not in cat_name_lower and 'микрофон' not in cat_name_lower): relevant = False
            if (
                    'переключател' in feat_name_lower or 'ресурс нажатий' in feat_name_lower or 'кейкапов' in feat_name_lower) and 'клавиатур' not in cat_name_lower: relevant = False
            if (
                    'сенсор' in feat_name_lower or 'ускорение' in feat_name_lower or 'dpi' in feat_name_lower or 'кнопок' in feat_name_lower) and 'мышь' not in cat_name_lower: relevant = False
            if 'коврик' in cat_name_lower and not any(
                    s in feat_name_lower for s in
                    ['материал', 'размер', 'цвет', 'толщина', 'покрытие']): relevant = False

            if relevant or random.random() < 0.05:
                try:
                    value = get_realistic_feature_value(feature.name, fake)
                    ProductFeatureValue.objects.create(product=product, feature=feature, value=value)
                    product_features.add(feature.id)
                    used_features_count += 1
                except Exception as e:
                    feature_creation_errors += 1

    if feature_creation_errors:
        print(f"Finished creating product features with {feature_creation_errors} minor errors (skipped).")
    else:
        print("Product features created.")

    print(f"Creating {REVIEW_COUNT} reviews...")
    reviews_created = 0
    review_skipped = 0
    if products and users:
        for i in range(REVIEW_COUNT):
            user = random.choice(users)
            product = random.choice(products)
            rating = random.randint(1, 5)
            text = fake.paragraph(nb_sentences=random.randint(2, 6))

            if random.random() > 0.7:
                text = f"**{fake.catch_phrase()}**\n\n{text}"
            is_approved = random.random() > 0.15

            review, created = Review.objects.get_or_create(
                product=product,
                user=user,
                defaults={
                    'rating': rating,
                    'text': text,
                    'is_approved': is_approved
                }
            )
            if created:
                reviews_created += 1
            else:
                review_skipped += 1

    print(f"{reviews_created} reviews created ({review_skipped} skipped due to uniqueness).")

    print(f"Creating {ORDER_COUNT} orders...")
    orders = []
    for _ in range(ORDER_COUNT):
        user = random.choice(users)
        order_status = random.choice(order_statuses)
        order_time = timezone.now() - timedelta(days=random.randint(0, 120), hours=random.randint(0, 23))
        order = Order.objects.create(
            user=user, delivery_address=fake.address(), contact_phone=fake.phone_number(),
            status=order_status, payment=random.choice(payment_methods),
            delivery_method=random.choice(delivery_methods), order_date=order_time)
        orders.append(order)
    print("Orders created.")

    print("Creating order items...")
    total_items = 0
    if orders and products:
        for order in orders:
            num_items_in_order = random.randint(1, 6)
            order_products = random.sample(products, min(num_items_in_order, len(products))) if len(
                products) >= num_items_in_order else random.choices(products, k=num_items_in_order)
            for product in order_products:
                qty = random.randint(1, 3)
                OrderItem.objects.create(order=order, product=product, qty=qty, price_per_item=product.price)
                total_items += 1
        print(f"{total_items} order items created.")
    else:
        print("Skipped creating order items (no orders or products).")

    print(f"Creating {BANNER_COUNT} banners...")
    positions = [choice[0] for choice in Banner.POSITION_CHOICES]
    now = timezone.now()
    banners = []
    banner_titles = ["Горячие Новинки!", "Распродажа Мышей", "Клавиатуры Мечты", "Звук Победы", "Идеальный Коврик",
                     "Мониторы QHD 165Гц", "Геймпады для Профи", "Веб-камеры Full HD", "Аксессуары Razer",
                     "Скидки Logitech G", "HyperX Cloud", "Скидка Недели!", "Киберпонедельник!", "Финальная Распродажа",
                     "Летний Гейминг Фест"]
    for i in range(BANNER_COUNT):
        title = random.choice(banner_titles) + f" #{random.randint(100, 999)}"
        start = now - timedelta(days=random.randint(0, 10))
        end = start + timedelta(days=random.randint(7, 45))
        banner = Banner.objects.create(
            title=title, image=None, link_url=fake.url(),
            start_date=start, end_date=end, position=random.choice(positions),
            is_active=random.random() > 0.15)
        banners.append(banner)
    print("Banners created.")

    print("Creating banner targets...")
    target_types = [choice[0] for choice in BannerTarget.TARGET_TYPE_CHOICES]
    banner_target_errors = 0
    if banners:
        for banner in banners:
            num_targets = random.randint(1, 3)
            targets_created = 0
            possible_targets = []
            if products: possible_targets.extend(
                [('product', p.id) for p in random.sample(products, min(5, len(products)))])
            if brands: possible_targets.extend([('brand', b.id) for b in random.sample(brands, min(3, len(brands)))])
            if categories: possible_targets.extend(
                [('category', c.id) for c in random.sample(categories, min(3, len(categories)))])
            random.shuffle(possible_targets)

            for target_type, target_id in possible_targets:
                if targets_created >= num_targets: break
                try:
                    BannerTarget.objects.update_or_create(banner=banner, target_type=target_type, target_id=target_id)
                    targets_created += 1
                except Exception as e:
                    banner_target_errors += 1
        if banner_target_errors:
            print(f"Finished creating banner targets with {banner_target_errors} minor errors.")
        else:
            print("Banner targets created.")
    else:
        print("Skipped creating banner targets (no banners).")

    print(f"Creating {PROMOTION_COUNT} promotions...")
    discount_types = [choice[0] for choice in Promotion.DISCOUNT_TYPE_CHOICES]
    promotions = []
    promo_names = ["Весеннее Обновление", "Кибер Май", "Летний Ценопад", "Назад в Игру!", "Черная Пятница Предзаказ",
                   "Новогодние Скидки", "Скидка на Комплекты", "Ликвидация Коллекции", "Геймерский Уикенд", "Техно Бум"]
    for i in range(PROMOTION_COUNT):
        name = random.choice(promo_names) + f" {fake.year()}"
        discount_type = random.choice(discount_types)
        if discount_type == 'percentage':
            discount_value = Decimal(random.choice([5, 10, 15, 20, 25, 30, 40]))
        elif discount_type == 'fixed':
            discount_value = Decimal(random.choice([100, 200, 300, 500, 1000, 1500, 2000, 3000, 5000]))
        else:
            base_price = round(Decimal(random.uniform(990.0, 29990.0)), 0);
            discount_value = base_price - Decimal(
                random.choice([0, 1, 10]))
        start = now - timedelta(days=random.randint(0, 7))
        end = start + timedelta(days=random.randint(5, 25))
        promotion = Promotion.objects.create(
            name=name, description=f"Специальное предложение: {fake.bs()}. {fake.text(max_nb_chars=150)}",
            discount_type=discount_type, discount_value=discount_value, start_date=start,
            end_date=end, is_active=random.random() > 0.1)
        promotions.append(promotion)
    print("Promotions created.")

    print("Creating promotional products...")
    promo_product_errors = 0
    if promotions and products:
        for promotion in promotions:
            num_promo_products = random.randint(8, 20)
            promo_products_sample = random.sample(products, min(num_promo_products, len(products)))
            for product in promo_products_sample:
                promo_price = product.price
                try:
                    if promotion.discount_type == 'percentage':
                        promo_price = round(product.price * (1 - promotion.discount_value / 100), 2)
                    elif promotion.discount_type == 'fixed':
                        promo_price = max(round(product.price - promotion.discount_value, 2), Decimal('1.00'))
                    elif promotion.discount_type == 'special_price':
                        promo_price = promotion.discount_value if promotion.discount_value < product.price else round(
                            product.price * Decimal('0.95'), 2)

                    PromotionalProduct.objects.update_or_create(
                        product=product, promotion=promotion,
                        defaults={'promotional_price': promo_price, 'is_featured': random.random() < 0.2})
                except Exception as e:
                    promo_product_errors += 1
        if promo_product_errors:
            print(f"Finished creating promotional products with {promo_product_errors} minor errors.")
        else:
            print("Promotional products created.")
    else:
        print("Skipped creating promotional products (no promotions or products).")

    print("\nFaker data generation finished successfully!")
    return HttpResponse(
        "База данных успешно заполнена увеличенным и более реалистичным набором фиктивных данных, включая отзывы.")


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешение позволяет редактировать объект только его владельцу (по полю 'user').
    Чтение разрешено всем.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return hasattr(obj, 'user') and obj.user == request.user


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = serializers.UserSerializer
    permission_classes = [permissions.IsAdminUser]


class OrderStatusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OrderStatus.objects.all()
    serializer_class = serializers.OrderStatusSerializer
    permission_classes = [permissions.AllowAny]


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all().order_by('name')
    serializer_class = serializers.BrandSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class FeatureViewSet(viewsets.ModelViewSet):
    queryset = Feature.objects.all().order_by('name')
    serializer_class = serializers.FeatureSerializer
    permission_classes = [permissions.IsAdminUser]


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        queryset = Review.objects.select_related('user', 'product').prefetch_related('images')
        product_id = self.request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if self.action == 'list':
            queryset = queryset.filter(is_approved=True)
        return queryset.order_by('-created_at')

    def _handle_uploaded_images(self, review_instance, is_update=False):
        uploaded_images_data = self.request.FILES.getlist('uploaded_images')

        if is_update:
            images_to_delete_ids = self.request.data.getlist('delete_images_ids')
            if images_to_delete_ids:
                try:
                    valid_ids = [int(id_str) for id_str in images_to_delete_ids]
                    review_instance.images.filter(id__in=valid_ids, review=review_instance).delete()
                except ValueError:
                    print("Warning: Invalid image ID provided for deletion during update.")

        max_images = 2
        current_image_count = review_instance.images.count()

        images_actually_added = 0
        for image_file in uploaded_images_data:
            if current_image_count + images_actually_added >= max_images:
                print(f"Warning: Maximum number of images ({max_images}) reached. Skipping additional files.")
                break
            ReviewImage.objects.create(review=review_instance, image=image_file)
            images_actually_added += 1

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review = serializer.save(user=request.user)
        self._handle_uploaded_images(review, is_update=False)

        instance_with_images = self.get_queryset().get(pk=review.pk)
        response_serializer = self.get_serializer(instance_with_images)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        review = serializer.save()
        self._handle_uploaded_images(review, is_update=True)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        instance_with_images = self.get_queryset().get(pk=instance.pk)
        response_serializer = self.get_serializer(instance_with_images)
        return Response(response_serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint для товаров. Поддерживает разные сериализаторы.
    Включает поиск через параметр ?search=...
    Автоматически аннотирует актуальную цену с учетом акций.
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend
    ]
    search_fields = [
        'name',
        'brand__name',
        'category__name',
    ]
    ordering_fields = ['name', 'price', 'created_at', 'average_rating']
    filterset_fields = ['category', 'brand']

    def get_queryset(self):
        """
        Базовый queryset с аннотацией текущей акционной цены.
        """
        now = timezone.now()

        active_promo_price_subquery = PromotionalProduct.objects.filter(
            product_id=OuterRef('pk'),
            promotion__is_active=True,
            promotion__start_date__lte=now,
            promotion__end_date__gte=now
        ).order_by('promotional_price').values('promotional_price')[:1]

        queryset = Product.objects.annotate(
            current_promotional_price=Subquery(active_promo_price_subquery,
                                               output_field=DecimalField(max_digits=12, decimal_places=2)),
            actual_price=Coalesce(
                Case(
                    When(current_promotional_price__isnull=False, current_promotional_price__lt=F('price'),
                         then=F('current_promotional_price')),
                    default=F('price'),
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                ),
                F('price'),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        ).select_related(
            'category', 'brand'
        ).prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.filter(main_image=True), to_attr='main_image_list'),

            Prefetch('feature_values',
                     queryset=ProductFeatureValue.objects.select_related('feature').order_by('feature__name'))
        ).order_by('-created_at')

        return queryset

    def get_serializer_class(self):
        """Определяет сериализатор в зависимости от действия."""
        if self.action in ['list', 'search_suggestions']:
            return ProductListSerializer
        return ProductSerializer

    @action(detail=False, methods=['get'], url_path='search-suggestions')
    def search_suggestions(self, request, *args, **kwargs):
        """Возвращает ограниченный список товаров для подсказок поиска."""
        queryset = self.filter_queryset(self.get_queryset())
        limit = 10
        queryset = queryset[:limit]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        """Возвращает пагинированный список товаров."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = serializers.ProductImageSerializer
    permission_classes = [permissions.IsAdminUser]


class ProductFeatureValueViewSet(viewsets.ModelViewSet):
    queryset = ProductFeatureValue.objects.all().select_related('product', 'feature')
    serializer_class = serializers.ProductFeatureValueSerializer
    permission_classes = [permissions.IsAdminUser]


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False): return Order.objects.none()
        user = self.request.user
        if not user or not user.is_authenticated:
            return Order.objects.none()
        base_qs = Order.objects.select_related(
            'user', 'status', 'payment', 'delivery_method'
        ).prefetch_related(
            Prefetch('items', queryset=OrderItem.objects.select_related('product'))
        )
        if user.is_staff or user.is_superuser:
            return base_qs.all().order_by('-order_date')
        return base_qs.filter(user=user).order_by('-order_date')

    def create(self, request, *args, **kwargs):
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        validated_data = create_serializer.validated_data
        user = request.user

        try:

            with transaction.atomic():

                cart_items = CartItem.objects.filter(user=user).select_for_update().select_related('product')

                if not cart_items.exists():
                    return Response({"detail": "Ваша корзина пуста."}, status=status.HTTP_400_BAD_REQUEST)

                products_to_update = []
                for item in cart_items:
                    product = item.product
                    if product.stock < item.quantity:
                        return Response(
                            {
                                "detail": f"Недостаточно товара '{product.name}' на складе. Доступно: {product.stock} шт., в заказе: {item.quantity} шт."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    product.stock -= item.quantity
                    products_to_update.append(product)

                new_status, _ = OrderStatus.objects.get_or_create(status="Новый",
                                                                  defaults={'description': 'Заказ создан'})

                order = Order.objects.create(
                    user=user,
                    delivery_address=validated_data['delivery_address'],
                    contact_phone=validated_data['contact_phone'],
                    delivery_method=validated_data['delivery_method'],
                    payment=validated_data['payment_method'],
                    status=new_status
                )

                order_items_to_create = [
                    OrderItem(
                        order=order,
                        product=item.product,
                        qty=item.quantity,
                        price_per_item=item.current_price_per_item
                    ) for item in cart_items
                ]
                OrderItem.objects.bulk_create(order_items_to_create)

                Product.objects.bulk_update(products_to_update, ['stock'])

                cart_items.delete()

                final_order = self.get_queryset().get(pk=order.pk)
                read_serializer = OrderSerializer(final_order, context=self.get_serializer_context())
                return Response(read_serializer.data, status=status.HTTP_201_CREATED,
                                headers=self.get_success_headers(read_serializer.data))

        except Exception as e:

            import traceback
            print(f"Error creating order for user {user.id}: {e}")
            print(traceback.format_exc())
            return Response({"detail": "Произошла непредвиденная ошибка при создании заказа."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeliveryMethodViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint для просмотра способов доставки."""
    queryset = DeliveryMethod.objects.all().order_by('id')
    serializer_class = DeliveryMethodSerializer
    permission_classes = [permissions.AllowAny]


class PaymentMethodViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint для просмотра способов оплаты."""
    queryset = PaymentMethod.objects.all().order_by('id')
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.AllowAny]


class OrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False): return OrderItem.objects.none()
        user = self.request.user
        base_qs = OrderItem.objects.select_related('order', 'product')
        if user.is_staff or user.is_superuser:
            return base_qs.all()
        return base_qs.filter(order__user=user)

    http_method_names = ['get', 'head', 'options', 'delete']


class BannerViewSet(viewsets.ModelViewSet):
    queryset = Banner.objects.all().prefetch_related('targets').order_by('-created_at')
    serializer_class = serializers.BannerSerializer
    permission_classes = [permissions.IsAdminUser]


class BannerTargetViewSet(viewsets.ModelViewSet):
    queryset = BannerTarget.objects.all().select_related('banner')
    serializer_class = serializers.BannerTargetSerializer
    permission_classes = [permissions.IsAdminUser]


class PromotionViewSet(viewsets.ModelViewSet):
    """
    API endpoint для управления акциями (админ).
    GET list возвращает только активные акции для всех пользователей.
    """

    permission_classes = [permissions.IsAdminUser]

    serializer_class = serializers.PromotionSerializer

    def get_permissions(self):
        """
        Разрешаем чтение списка (list) и конкретной акции (retrieve) всем,
        а остальные действия - только админам.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Фильтрует акции:
        - Для 'list' и 'retrieve': только активные и в текущем диапазоне дат.
        - Для админов (другие actions): все акции.
        """
        user = self.request.user
        now = timezone.now()
        base_queryset = Promotion.objects.all().prefetch_related(

            Prefetch(
                'promo_products',
                queryset=PromotionalProduct.objects.select_related(
                    'product', 'product__brand'
                ).prefetch_related(
                    Prefetch(
                        'product__images',
                        queryset=ProductImage.objects.filter(main_image=True),
                        to_attr='main_image_list'
                    )
                ).filter(

                )
            )
        ).order_by('-start_date', 'name')

        if self.action in ['list', 'retrieve']:
            return base_queryset.filter(
                is_active=True,
                start_date__lte=now,
                end_date__gte=now
            )

        elif user and user.is_staff:
            return base_queryset
        else:

            return Promotion.objects.none()


class PromotionalProductViewSet(viewsets.ModelViewSet):
    queryset = PromotionalProduct.objects.all().select_related('product', 'promotion').order_by('promotion__name',
                                                                                                'product__name')
    serializer_class = serializers.PromotionalProductSerializer
    permission_classes = [permissions.IsAdminUser]


class HomepageDataView(APIView):
    """
    Агрегированный эндпоинт для данных главной страницы (Class-Based View).
    Включает: случайный активный баннер, список категорий,
              акционные товары и последние товары (с актуальными ценами).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        now = timezone.now()

        active_promo_price_subquery = PromotionalProduct.objects.filter(
            product_id=OuterRef('pk'),
            promotion__is_active=True,
            promotion__start_date__lte=now,
            promotion__end_date__gte=now
        ).order_by('promotional_price').values('promotional_price')[:1]

        def annotate_product_prices(queryset):
            return queryset.annotate(
                current_promotional_price=Subquery(active_promo_price_subquery,
                                                   output_field=DecimalField(max_digits=12, decimal_places=2)),
                actual_price=Coalesce(
                    Case(
                        When(current_promotional_price__isnull=False, current_promotional_price__lt=F('price'),
                             then=F('current_promotional_price')),
                        default=F('price'),
                        output_field=DecimalField(max_digits=12, decimal_places=2)
                    ),
                    F('price'),
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                )
            )

        active_banners = Banner.objects.filter(is_active=True, start_date__lte=now, end_date__gte=now,
                                               position='home_top')
        random_banner = random.choice(list(active_banners)) if active_banners.exists() else None
        banner_serializer = BannerSerializer(random_banner, context={'request': request}) if random_banner else None

        categories = Category.objects.all().order_by('name')
        category_serializer = CategorySerializer(categories, many=True, context={'request': request})

        promo_products_base_qs = PromotionalProduct.objects.filter(
            promotion__is_active=True,
            promotion__start_date__lte=now,
            promotion__end_date__gte=now
        ).select_related('promotion')

        product_ids_in_promos = promo_products_base_qs.values_list('product_id', flat=True).distinct()

        annotated_promo_products_qs = annotate_product_prices(
            Product.objects.filter(id__in=list(product_ids_in_promos))
        ).select_related(
            'category', 'brand'
        ).prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.filter(main_image=True), to_attr='main_image_list')
        ).order_by('?')[:10]

        promotional_items_serializer = ProductListSerializer(annotated_promo_products_qs, many=True,
                                                             context={'request': request})

        latest_products_qs_base = Product.objects.all().order_by('-created_at')[:12]
        latest_product_ids = list(latest_products_qs_base.values_list('id', flat=True))

        annotated_latest_products_qs = annotate_product_prices(
            Product.objects.filter(id__in=latest_product_ids)
        ).select_related(
            'category', 'brand'
        ).prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.filter(main_image=True), to_attr='main_image_list')
        ).order_by('-created_at')

        latest_products_serializer = ProductListSerializer(annotated_latest_products_qs, many=True,
                                                           context={'request': request})

        data = {
            'banner': banner_serializer.data if banner_serializer else None,
            'categories': category_serializer.data,
            'promotions': promotional_items_serializer.data,
            'latest_products': latest_products_serializer.data,
        }
        return Response(data)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint для категорий.
    - list: Возвращает список категорий.
    - retrieve: Возвращает детали категории, включая список товаров с актуальными ценами.
    Поддерживает фильтрацию и сортировку товаров внутри категории при retrieve.
    """
    queryset = Category.objects.all().order_by('name')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    product_filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    product_ordering_fields = ['name', 'price', 'created_at', 'average_rating']
    product_filterset_fields = ['brand']

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action == 'retrieve':
            return CategoryDetailSerializer
        return CategorySerializer

    def get_queryset(self):
        """
        Базовый queryset для категорий. Для retrieve добавляет prefetch
        для товаров с аннотированными ценами и возможностью фильтрации/сортировки.
        """
        queryset = super().get_queryset()

        if self.action == 'retrieve' and 'pk' in self.kwargs:

            products_base_qs = Product.objects.all()

            products_with_prices_qs = annotate_product_prices(products_base_qs)

            class DummyProductFilterView:
                filter_backends = self.product_filter_backends
                ordering_fields = self.product_ordering_fields
                filterset_fields = self.product_filterset_fields

                request = self.request

                def get_queryset(self): return products_with_prices_qs

                format_kwarg = None

            filter_view = DummyProductFilterView()
            filtered_sorted_products_qs = products_with_prices_qs

            for backend in list(filter_view.filter_backends):

                if backend == filters.SearchFilter: continue
                filtered_sorted_products_qs = backend().filter_queryset(
                    self.request,
                    filtered_sorted_products_qs,
                    filter_view
                )

            final_products_qs = filtered_sorted_products_qs.select_related(
                'brand'
            ).prefetch_related(
                Prefetch('images', queryset=ProductImage.objects.filter(main_image=True), to_attr='main_image_list')
            ).order_by('-created_at')

            queryset = queryset.prefetch_related(
                Prefetch(
                    'products',
                    queryset=final_products_qs
                )
            )

        return queryset


User = get_user_model()


class LoginOrRegisterView(APIView):
    """
    Единый эндпоинт для входа или регистрации пользователя.
    Принимает username и password.
    Если пользователь существует - пытается войти.
    Если не существует - регистрирует нового.
    Возвращает токен и данные пользователя при успехе.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginOrRegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')
        user = None
        token = None

        try:
            user_exists = User.objects.get(username=username)

            user = authenticate(request=request, username=username, password=password)
            if user:

                token, _ = Token.objects.get_or_create(user=user)

                response_data = {'token': token.key, 'user': user}
                response_serializer = self.serializer_class(response_data)
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            else:

                return Response(
                    {"detail": "Неверный пароль."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        except User.DoesNotExist:

            try:
                user = User.objects.create_user(username=username, password=password)

                token = Token.objects.create(user=user)

                response_data = {'token': token.key, 'user': user}
                response_serializer = self.serializer_class(response_data)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:

                return Response(
                    {"detail": f"Ошибка при регистрации: {e}"},
                    status=status.HTTP_400_BAD_REQUEST
                )


class CartItemViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = CartItemSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return CartItem.objects.none()
        return CartItem.objects.filter(user=user).select_related(
            'product', 'product__brand'
        ).prefetch_related(
            Prefetch('product__images', queryset=ProductImage.objects.filter(main_image=True),
                     to_attr='main_image_list')
        ).order_by('-added_at')

    def perform_create(self, serializer):
        user = self.request.user
        product = serializer.validated_data.get('product')
        quantity = serializer.validated_data.get('quantity', 1)

        current_quantity_in_cart = 0
        cart_item, created = CartItem.objects.get_or_create(
            user=user,
            product=product,
            defaults={'quantity': 0}
        )
        if not created:
            current_quantity_in_cart = cart_item.quantity

        total_quantity_needed = current_quantity_in_cart + quantity

        if product.stock < total_quantity_needed:
            raise serializers.ValidationError(
                f"Недостаточно товара '{product.name}' на складе. Доступно: {product.stock} шт., в корзине уже: {current_quantity_in_cart} шт."
            )

        cart_item.quantity += quantity
        cart_item.save()
        serializer.instance = cart_item

    def perform_update(self, serializer):
        product = serializer.instance.product
        new_quantity = serializer.validated_data.get('quantity')

        if product.stock < new_quantity:
            raise serializers.ValidationError(
                f"Недостаточно товара '{product.name}' на складе. Доступно: {product.stock} шт."
            )

        serializer.save()
