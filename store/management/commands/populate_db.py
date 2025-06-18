import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db import IntegrityError, transaction
from faker import Faker

from store.models import (
    User, Category, Brand, Feature, OrderStatus, PaymentMethod,
    DeliveryMethod, Product, ProductImage, ProductFeatureValue,
    Order, OrderItem, Banner, BannerTarget, Promotion, PromotionalProduct,
    Review, ReviewImage, CartItem, WishlistItem
)


def get_realistic_feature_value(feature_name, fake):
    name_lower = feature_name.lower()
    if 'подсветка' in name_lower: return random.choice(
        ['RGB', 'Одноцветная (красная)', 'Нет', 'Настраиваемая RGB', 'Белая'])
    if 'тип подключения' in name_lower: return random.choice(
        ['Проводное USB', 'Беспроводное 2.4GHz', 'Bluetooth 5.0', 'Проводное + Bluetooth', 'USB Type-C'])
    if 'тип сенсора' in name_lower: return random.choice(
        ['Оптический', 'Лазерный', 'Оптический PixArt PMW3360', 'Оптический HERO 25K', 'Оптический Focus+'])
    if 'dpi' in name_lower or 'разрешение сенсора' in name_lower: return f'{random.choice([800, 1600, 3200, 6400, 12000, 16000, 19000, 26000])} DPI'
    if 'тип переключателей' in name_lower: return random.choice(
        ['Механические (Cherry MX Red)', 'Механические (Outemu Blue)', 'Мембранные',
         'Оптико-механические (Razer Clicky)', 'Ножничные', 'Механические (Gateron Brown)',
         'Оптические (LK Light Strike)'])
    if 'частота опроса' in name_lower: return f'{random.choice([125, 500, 1000, 2000, 4000, 8000])} Гц'
    if 'материал' in name_lower and 'амбушюр' not in name_lower and 'кейкапов' not in name_lower: return random.choice(
        ['Пластик ABS', 'Алюминий', 'Магниевый сплав', 'Металл + Пластик', 'PBT пластик'])
    if 'цвет' in name_lower: return fake.color_name()
    if 'вес' in name_lower: return f'{random.randint(50, 1200)} г'
    if 'размер' in name_lower: return random.choice(
        ['Компактный (60%)', 'TKL (80%)', 'Стандартный (100%)', 'Полноразмерный', 'XL', 'M', 'L'])
    if 'диагональ' in name_lower: return f'{random.choice([23.8, 24.5, 27, 31.5, 34, 49])}'
    if 'разрешение' in name_lower and 'сенсора' not in name_lower: return random.choice(
        ['1920x1080 (Full HD)', '2560x1440 (QHD)', '3440x1440 (UWQHD)', '3840x2160 (4K UHD)'])
    if 'частота обновления' in name_lower: return f'{random.choice([60, 75, 100, 144, 165, 170, 240, 360])}'
    if 'тип матрицы' in name_lower: return random.choice(['IPS', 'VA', 'TN', 'Fast IPS', 'OLED', 'QD-OLED'])
    if 'совместимость' in name_lower: return random.choice(
        ['PC', 'PC, MacOS', 'PC, PS5, Xbox Series S/X', 'PC, PS4/5', 'PC, MacOS, Linux'])
    return fake.word() if random.random() > 0.5 else str(random.randint(1, 500))


class Command(BaseCommand):
    help = 'Populates the database with a set of realistic fake data.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting database population...'))

        fake = Faker("ru_RU")
        now = timezone.now()

        USER_COUNT = 20;
        BRAND_COUNT = 15;
        FEATURE_COUNT = 35
        PRODUCT_COUNT = 100;
        ORDER_COUNT = 50;
        REVIEW_COUNT_PER_PRODUCT_AVG = 4
        BANNER_COUNT = 10;
        PROMOTION_COUNT = 8

        self.stdout.write('Deleting old data...')

        WishlistItem.objects.all().delete();
        CartItem.objects.all().delete();
        ReviewImage.objects.all().delete()
        Review.objects.all().delete();
        PromotionalProduct.objects.all().delete();
        BannerTarget.objects.all().delete()
        OrderItem.objects.all().delete();
        Order.objects.all().delete();
        Banner.objects.all().delete()
        Promotion.objects.all().delete();
        ProductImage.objects.all().delete();
        ProductFeatureValue.objects.all().delete()
        Product.objects.all().delete();
        Feature.objects.all().delete();
        Category.objects.all().delete()
        Brand.objects.all().delete();
        OrderStatus.objects.all().delete();
        PaymentMethod.objects.all().delete()
        DeliveryMethod.objects.all().delete();
        User.objects.exclude(is_superuser=True).delete()
        self.stdout.write(self.style.SUCCESS('Old data deleted.'))

        users = [
            User.objects.create_user(username=fake.unique.user_name(), email=fake.unique.email(), password="password",
                                     first_name=fake.first_name(), last_name=fake.last_name()) for _ in
            range(USER_COUNT)]
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.stdout.write(f'{len(users)} users created.')

        category_names = ['Мыши', 'Клавиатуры', 'Гарнитуры', 'Коврики для мыши', 'Мониторы', 'Геймпады', 'Веб-камеры',
                          'Микрофоны', 'Кресла', 'Аксессуары']
        categories = [
            Category.objects.get_or_create(name=name, defaults={'description': f"Всё для категории '{name}'."})[0] for
            name in category_names]
        brand_names = ['Razer', 'Logitech G', 'SteelSeries', 'HyperX', 'Corsair', 'ASUS ROG', 'Zowie', 'Glorious',
                       'Dark Project', 'A4Tech Bloody']
        brands = [Brand.objects.get_or_create(name=name, defaults={'description': f"Игровая периферия от {name}."})[0]
                  for name in brand_names]
        feature_names = ['Тип сенсора', 'Разрешение сенсора (DPI)', 'Подсветка', 'Тип подключения',
                         'Тип переключателей', 'Цвет', 'Вес', 'Размер', 'Тип матрицы']
        features = [Feature.objects.get_or_create(name=name)[0] for name in feature_names]
        order_statuses = [OrderStatus.objects.get_or_create(status=s[0], defaults={'description': s[1]})[0] for s in
                          [("Новый", "Заказ создан"), ("Доставлен", "Заказ получен"), ("Отменен", "Заказ отменен")]]
        payment_methods = [PaymentMethod.objects.get_or_create(method_name=m)[0] for m in
                           ["Онлайн картой", "Наличными при получении"]]
        delivery_methods = [DeliveryMethod.objects.get_or_create(method_name=m)[0] for m in
                            ["Курьерская доставка", "Самовывоз"]]
        self.stdout.write(' справочники созданы.')

        products = []
        for _ in range(PRODUCT_COUNT):
            category = random.choice(categories);
            brand = random.choice(brands)
            product = Product.objects.create(name=f"{brand.name} {category.name} {fake.word().capitalize()}",
                                             price=Decimal(random.randrange(1000, 30000, 100)), category=category,
                                             brand=brand, stock=random.choice([0, 5, 10, 20, 50]))
            products.append(product)
        self.stdout.write(f'{len(products)} products created.')

        for i in range(PROMOTION_COUNT):
            promo = Promotion.objects.create(
                name=f"Акция #{i + 1}",
                discount_type='percentage',
                discount_value=random.randint(10, 30),
                start_date=now - timedelta(days=1),
                end_date=now + timedelta(days=10),
                is_active=True
            )
            for product in random.sample(products, min(len(products), 5)):
                discount_multiplier = Decimal('1') - (promo.discount_value / Decimal('100'))
                promo_price = product.price * discount_multiplier

                PromotionalProduct.objects.create(
                    product=product,
                    promotion=promo,
                    promotional_price=promo_price.quantize(Decimal('0.01'))
                )
        self.stdout.write(f'{PROMOTION_COUNT} promotions with products created.')

        for i in range(BANNER_COUNT):
            Banner.objects.create(title=f"Баннер #{i + 1}", link_url="https://example.com", position='home_top',
                                  start_date=now - timedelta(days=1), end_date=now + timedelta(days=10), is_active=True)
        self.stdout.write(f'{BANNER_COUNT} banners created.')

        for _ in range(ORDER_COUNT):
            user = random.choice(users)
            order = Order.objects.create(user=user, delivery_address=fake.address(), contact_phone=fake.phone_number(),
                                         status=random.choice(order_statuses), payment=random.choice(payment_methods),
                                         delivery_method=random.choice(delivery_methods))
            for _ in range(random.randint(1, 4)):
                product = random.choice(products)
                if not OrderItem.objects.filter(order=order, product=product).exists():
                    OrderItem.objects.create(order=order, product=product, qty=random.randint(1, 3),
                                             price_per_item=product.price)
        self.stdout.write(f'{ORDER_COUNT} orders created.')

        self.stdout.write(self.style.SUCCESS('Database population finished successfully!'))
