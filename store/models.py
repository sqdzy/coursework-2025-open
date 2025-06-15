from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Avg, Min
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone


class User(AbstractUser):
    groups = models.ManyToManyField(
        Group,
        related_name="store_user_groups",
        blank=True,
        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
        verbose_name="groups"
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="store_user_permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions"
    )
    created_at = models.DateTimeField("Дата регистрации", auto_now_add=True)

    wishlist_products = models.ManyToManyField(
        'Product',
        through='WishlistItem',
        related_name='wishlisted_by_users',
        blank=True,
        verbose_name='Товары в списке желаний'
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username or f"User {self.pk}"


class Category(models.Model):
    name = models.CharField('Название категории', max_length=255)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField('Название бренда', max_length=255)
    description = models.TextField('Описание', blank=True)
    brand_banner = models.ImageField('Баннер', upload_to='brands/', null=True, blank=True)

    class Meta:
        verbose_name = 'Бренд'
        verbose_name_plural = 'Бренды'

    def __str__(self):
        return self.name


class Feature(models.Model):
    name = models.CharField('Название характеристики', max_length=255)

    class Meta:
        verbose_name = 'Характеристика'
        verbose_name_plural = 'Характеристики'

    def __str__(self):
        return self.name


class OrderStatus(models.Model):
    status = models.CharField('Статус заказа', max_length=255)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'Статус заказа'
        verbose_name_plural = 'Статусы заказов'

    def __str__(self):
        return self.status


class PaymentMethod(models.Model):
    method_name = models.CharField('Способ оплаты', max_length=50)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'Способ оплаты'
        verbose_name_plural = 'Способы оплаты'

    def __str__(self):
        return self.method_name


class DeliveryMethod(models.Model):
    method_name = models.CharField('Способ доставки', max_length=50)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'Способ доставки'
        verbose_name_plural = 'Способы доставки'

    def __str__(self):
        return self.method_name


class Product(models.Model):
    name = models.CharField('Название товара', max_length=255)
    price = models.DecimalField('Цена', max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    category = models.ForeignKey(Category, verbose_name='Категория', on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, verbose_name='Бренд', on_delete=models.CASCADE, related_name='products')
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True, db_index=True)
    stock = models.PositiveIntegerField('Количество на складе', default=0, help_text='Количество доступных единиц товара')

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_average_rating(self):
        avg = self.reviews.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg is not None else 0.0

    def get_review_count(self):
        return self.reviews.filter(is_approved=True).count()


class ProductImage(models.Model):
    product = models.ForeignKey(Product, verbose_name='Товар', on_delete=models.CASCADE,
                                related_name='images')
    image = models.ImageField('Изображение', upload_to='products/', null=True, blank=True)
    main_image = models.BooleanField('Главное изображение', default=False)

    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'

    def __str__(self):
        product_name = self.product.name if self.product else "Unknown Product"
        return f"Изображение для {product_name}"


class ProductFeatureValue(models.Model):
    product = models.ForeignKey(Product, verbose_name='Товар', on_delete=models.CASCADE,
                                related_name='feature_values')
    feature = models.ForeignKey(Feature, verbose_name='Характеристика', on_delete=models.CASCADE,
                                related_name='product_values')
    value = models.CharField('Значение', max_length=255)

    class Meta:
        verbose_name = 'Значение характеристики'
        verbose_name_plural = 'Значения характеристик'

        unique_together = ('product', 'feature')

    def __str__(self):
        feature_name = self.feature.name if self.feature else "Unknown Feature"
        return f"{feature_name}: {self.value}"


def review_image_upload_path(instance, filename):
    return f'reviews/{instance.review.id}/{filename}'

class Review(models.Model):
    RATING_CHOICES = [ (i, str(i)) for i in range(1, 6) ]
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='reviews', verbose_name='Товар')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews', verbose_name='Пользователь')
    rating = models.IntegerField('Оценка', choices=RATING_CHOICES, db_index=True)
    text = models.TextField('Текст отзыва')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    is_approved = models.BooleanField('Одобрен', default=False, db_index=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
        unique_together = ('product', 'user')

    def __str__(self):
        return f"Отзыв от {self.user.username} на {self.product.name} ({self.rating}*)"


class ReviewImage(models.Model):
    review = models.ForeignKey(Review, related_name='images', on_delete=models.CASCADE, verbose_name='Отзыв')
    image = models.ImageField('Изображение', upload_to=review_image_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Изображение отзыва'
        verbose_name_plural = 'Изображения отзывов'
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Изображение для отзыва {self.review.id}"
class Order(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE,
                             related_name='orders')
    order_date = models.DateTimeField('Дата заказа', auto_now_add=True)
    delivery_address = models.TextField('Адрес доставки')
    contact_phone = models.CharField('Контактный телефон', max_length=20)
    status = models.ForeignKey(OrderStatus, verbose_name='Статус заказа', on_delete=models.SET_NULL, null=True,
                               blank=True, related_name='orders')
    payment = models.ForeignKey(PaymentMethod, verbose_name='Способ оплаты', on_delete=models.SET_NULL, null=True,
                                blank=True, related_name='orders')
    delivery_method = models.ForeignKey(DeliveryMethod, verbose_name='Способ доставки', on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='orders')
    total_amount = models.DecimalField('Итоговая сумма', max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-order_date']

    def __str__(self):
        user_str = self.user.username if self.user else "Unknown User"
        return f"Заказ #{self.id} от {user_str}"

    def update_total_amount(self):
        """Пересчитывает и сохраняет общую сумму заказа на основе его позиций."""
        total = self.items.aggregate(
            total=models.Sum(models.F('qty') * models.F('price_per_item'))
        )['total']
        self.total_amount = total if total is not None else Decimal('0.00')
        self.save(update_fields=['total_amount'])

    @property
    def calculated_total_amount(self):
        total = self.items.aggregate(
            total=models.Sum(models.F('qty') * models.F('price_per_item'))
        )['total']
        return total if total is not None else Decimal('0.00')


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='Заказ', on_delete=models.CASCADE,
                              related_name='items')
    product = models.ForeignKey(Product, verbose_name='Товар', on_delete=models.PROTECT, related_name='order_items')
    qty = models.PositiveIntegerField('Количество', validators=[MinValueValidator(1)])
    price_per_item = models.DecimalField('Цена за единицу', max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

        unique_together = ('order', 'product')

    def __str__(self):
        product_str = self.product.name if self.product else "Unknown Product"
        order_id = self.order.id if self.order else "Unknown Order"
        return f"{product_str} ({self.qty} шт.) (Заказ #{order_id})"

    @property
    def total_item_price(self):
        return (self.qty or 0) * (self.price_per_item or Decimal('0.00'))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.order:
            self.order.update_total_amount()

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        if order:
            order.update_total_amount()


class Banner(models.Model):
    POSITION_CHOICES = [
        ('home_top', 'Главная верх'),
        ('home_middle', 'Главная середина'),
        ('category_top', 'Верх категории'),
        ('product_page', 'Страница товара'),
        ('sidebar', 'Боковая панель'),
    ]

    title = models.CharField('Заголовок', max_length=100)
    image = models.ImageField('Изображение', upload_to='banners/')
    link_url = models.URLField('URL ссылки', max_length=255)
    start_date = models.DateTimeField('Дата начала', null=True, blank=True)
    end_date = models.DateTimeField('Дата окончания', null=True, blank=True)
    position = models.CharField('Позиция на сайте', max_length=50, choices=POSITION_CHOICES, db_index=True)
    is_active = models.BooleanField('Активен', default=True, db_index=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    sort_order = models.PositiveIntegerField('Порядок сортировки', default=0)

    class Meta:
        verbose_name = 'Баннер'
        verbose_name_plural = 'Баннеры'
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return self.title

    @property
    def is_currently_active(self):
        """Проверяет, активен ли баннер в данный момент времени."""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True


class BannerTarget(models.Model):
    TARGET_TYPE_CHOICES = [
        ('product', 'Товар'),
        ('brand', 'Бренд'),
        ('category', 'Категория'),
    ]

    banner = models.ForeignKey(Banner, verbose_name='Баннер', on_delete=models.CASCADE, related_name='targets')
    target_type = models.CharField('Тип цели', max_length=50, choices=TARGET_TYPE_CHOICES)

    target_id = models.PositiveIntegerField('ID цели')

    class Meta:
        verbose_name = 'Цель баннера'
        verbose_name_plural = 'Цели баннеров'
        unique_together = ('banner', 'target_type', 'target_id')

    def __str__(self):
        banner_title = self.banner.title if self.banner else "Unknown Banner"
        return f"{banner_title} → {self.get_target_type_display()} #{self.target_id}"

    def get_target(self):
        """Возвращает связанный объект (Product, Brand, Category) или None."""
        model_map = {
            'product': Product,
            'brand': Brand,
            'category': Category,
        }
        model = model_map.get(self.target_type)
        if model:
            try:
                return model.objects.get(id=self.target_id)
            except model.DoesNotExist:
                return None
        return None


class Promotion(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Процент'),
        ('fixed', 'Фиксированная сумма'),
        ('special_price', 'Специальная цена'),
    ]

    name = models.CharField('Название акции', max_length=100)
    description = models.TextField('Описание', blank=True)
    discount_type = models.CharField('Тип скидки', max_length=50, choices=DISCOUNT_TYPE_CHOICES,
                                     help_text="Тип скидки, применяемый к товарам (если не 'Специальная цена')")
    discount_value = models.DecimalField('Значение скидки', max_digits=10, decimal_places=2,
                                         help_text="Процент (напр., 10 для 10%) или фиксированная сумма", default=0.00)
    start_date = models.DateTimeField('Дата начала', default=timezone.now)
    end_date = models.DateTimeField('Дата окончания', null=True, blank=True)
    is_active = models.BooleanField('Активна', default=True, db_index=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Акция'
        verbose_name_plural = 'Акции'
        ordering = ['-start_date', 'name']

    def __str__(self):
        return self.name

    @property
    def is_currently_active(self):
        """Проверяет, активна ли акция в данный момент времени."""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True


class PromotionalProduct(models.Model):
    product = models.ForeignKey(Product, verbose_name='Товар', on_delete=models.CASCADE,
                                related_name='promotions')
    promotion = models.ForeignKey(Promotion, verbose_name='Акция', on_delete=models.CASCADE,
                                  related_name='promo_products')

    promotional_price = models.DecimalField(
        'Акционная цена',
        max_digits=12, decimal_places=2,
        null=True, blank=True,
        help_text="Укажите, если тип скидки 'Специальная цена'. Иначе будет рассчитана автоматически."
    )
    is_featured = models.BooleanField('Выделенный товар', default=False)

    class Meta:
        verbose_name = 'Акционный товар'
        verbose_name_plural = 'Акционные товары'
        unique_together = ('product', 'promotion')
        ordering = ['promotion', 'product__name']

    def __str__(self):
        product_str = self.product.name if self.product else "Unknown Product"
        promo_str = self.promotion.name if self.promotion else "Unknown Promotion"
        return f"{product_str} ({promo_str})"

    def get_calculated_promotional_price(self):
        """Рассчитывает акционную цену на основе типа скидки акции."""
        if not self.product or not self.promotion:
            return None

        base_price = self.product.price
        if base_price is None:
            return None

        if self.promotion.discount_type == 'special_price':
            return self.promotional_price
        elif self.promotion.discount_type == 'percentage':
            discount_amount = base_price * (self.promotion.discount_value / Decimal('100.0'))
            return max(Decimal('0.00'), base_price - discount_amount)
        elif self.promotion.discount_type == 'fixed':
            return max(Decimal('0.00'), base_price - self.promotion.discount_value)
        else:
            return base_price

    @property
    def effective_price(self):
        """Возвращает актуальную акционную цену (рассчитанную или указанную)."""
        return self.get_calculated_promotional_price()


class CartItem(models.Model):
    """Модель для хранения товара в корзине пользователя."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='Пользователь'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='Товар',
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(
        'Количество',
        default=1,
        validators=[MinValueValidator(1)]
    )
    added_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'Позиция в корзине'
        verbose_name_plural = 'Позиции в корзине'
        unique_together = ('user', 'product')
        ordering = ['-added_at']

    def __str__(self):
        user_str = self.user.username if self.user else "Unknown User"
        product_str = self.product.name if self.product else "Unknown Product"
        return f"{self.quantity} x {product_str} ({user_str})"

    @property
    def current_price_per_item(self):
        """Возвращает текущую актуальную цену за единицу товара (акционную или базовую)."""
        now = timezone.now()
        product = self.product

        if not product or product.price is None:
            return Decimal('0.00')

        base_price = product.price

        active_promo = PromotionalProduct.objects.filter(
            product=product,
            promotion__is_active=True,
            promotion__start_date__lte=now,
        ).filter(
            models.Q(promotion__end_date__isnull=True) | models.Q(promotion__end_date__gte=now)
        ).order_by(

            'promotional_price'
        ).first()

        min_effective_price = base_price
        has_active_promo = False

        active_promos = PromotionalProduct.objects.filter(
            product=product,
            promotion__is_active=True,
            promotion__start_date__lte=now,
        ).filter(
            models.Q(promotion__end_date__isnull=True) | models.Q(promotion__end_date__gte=now)
        ).select_related('promotion')

        for promo_product in active_promos:
            effective_price = promo_product.effective_price
            if effective_price is not None and effective_price < min_effective_price:
                min_effective_price = effective_price
                has_active_promo = True

        return min_effective_price

    @property
    def total_price(self):
        """Рассчитывает общую стоимость для этой позиции корзины."""
        quantity = self.quantity or 0
        return quantity * self.current_price_per_item


class WishlistItem(models.Model):
    """Промежуточная модель для связи User и Product (Список желаний)."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist_items',
        verbose_name='Пользователь'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlist_items',
        verbose_name='Товар'
    )
    added_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'Элемент списка желаний'
        verbose_name_plural = 'Элементы списка желаний'
        unique_together = ('user', 'product')
        ordering = ['-added_at']

    def __str__(self):
        user_str = self.user.username if self.user else "Unknown User"
        product_str = self.product.name if self.product else "Unknown Product"
        return f"{product_str} в списке желаний у {user_str}"
