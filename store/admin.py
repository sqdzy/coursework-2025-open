import datetime
import io
from decimal import Decimal, InvalidOperation

from django.contrib import admin
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.conf import settings

try:
    from weasyprint import HTML, CSS

    from weasyprint.urls import path2url

    WEASYPRINT_INSTALLED = True
except ImportError:
    WEASYPRINT_INSTALLED = False
    HTML = None
    CSS = None
    path2url = None
    print("WARNING: WeasyPrint is not installed or its dependencies are missing. PDF export will not work.")

from .models import (
    User, Category, Brand, Feature, OrderStatus, PaymentMethod,
    DeliveryMethod, Product, ProductImage, ProductFeatureValue,
    Order, OrderItem, Banner, BannerTarget, Promotion, PromotionalProduct,
    Review, CartItem, WishlistItem, ReviewImage
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "created_at", "is_staff",
                    "is_active")
    list_filter = ("is_staff", "is_active", "groups")
    search_fields = ("username", "first_name", "last_name", "email")
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительно', {"fields": ("created_at",)}),
    )
    readonly_fields = ("created_at", "last_login", "date_joined")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "product_count")
    search_fields = ("name",)
    list_display_links = ("name",)

    @admin.display(description="Кол-во товаров")
    def product_count(self, obj):
        return obj.products.count()


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "product_count")
    search_fields = ("name",)
    list_display_links = ("name",)

    @admin.display(description="Кол-во товаров")
    def product_count(self, obj):
        return obj.products.count()


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    list_display_links = ("name",)


@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ("status", "description")
    search_fields = ("status",)
    list_display_links = ("status",)


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("method_name", "description")
    search_fields = ("method_name",)
    list_display_links = ("method_name",)


@admin.register(DeliveryMethod)
class DeliveryMethodAdmin(admin.ModelAdmin):
    list_display = ("method_name", "description")
    search_fields = ("method_name",)
    list_display_links = ("method_name",)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('image_preview',)

    @admin.display(description="Предпросмотр")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<a href="{0}" target="_blank"><img src="{0}" style="max-height: 50px; max-width: 100px;" /></a>',
                obj.image.url)
        return "Нет изображения"


class ProductFeatureValueInline(admin.TabularInline):
    model = ProductFeatureValue
    extra = 2
    autocomplete_fields = ('feature',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "stock", "category_link", "brand_link", "created_at")
    list_filter = ("category", "brand", "created_at")
    search_fields = ("name", "brand__name", "category__name")
    date_hierarchy = "created_at"
    list_display_links = ("name",)
    list_editable = ("price", "stock")
    autocomplete_fields = ("category", "brand")
    readonly_fields = ("created_at", "average_rating_display", "review_count_display")
    inlines = [ProductImageInline, ProductFeatureValueInline]
    fieldsets = (
        (None, {'fields': ('name', 'price', 'stock', 'category', 'brand')}),
        ('Рейтинг (Авто)', {'fields': ('average_rating_display', 'review_count_display'), 'classes': ('collapse',)}),
        ('Даты', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )

    @admin.display(description="Категория", ordering='category__name')
    def category_link(self, obj):
        link = reverse("admin:store_category_change", args=[obj.category.id])
        return format_html('<a href="{}">{}</a>', link, obj.category.name)

    @admin.display(description="Бренд", ordering='brand__name')
    def brand_link(self, obj):
        link = reverse("admin:store_brand_change", args=[obj.brand.id])
        return format_html('<a href="{}">{}</a>', link, obj.brand.name)

    @admin.display(description="Рейтинг")
    def average_rating_display(self, obj):
        return obj.get_average_rating()

    @admin.display(description="Кол-во отзывов")
    def review_count_display(self, obj):
        return obj.get_review_count()


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ('product',)

    readonly_fields = ('product_link', 'price_per_item', 'total_item_price_display')
    fields = ('product_link', 'qty', 'price_per_item', 'total_item_price_display')

    @admin.display(description="Товар")
    def product_link(self, obj):
        if obj.product_id:
            try:
                link = reverse("admin:store_product_change", args=[obj.product_id])
                return format_html('<a href="{}">{}</a>', link, obj.product.name)
            except Product.DoesNotExist:
                return "Товар удален"
        return "-"

    @admin.display(description="Сумма")
    def total_item_price_display(self, obj):

        return f"{obj.total_item_price:.2f} ₽"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    actions = ['export_active_orders_to_pdf_weasyprint']

    list_display = ("id", "user_link", "order_date_formatted", "status", "calculated_total_amount")
    list_filter = ("status", "payment", "delivery_method", "order_date")
    search_fields = ("id", "user__username", "contact_phone", "delivery_address", "items__product__name")
    date_hierarchy = "order_date"
    list_display_links = ("id",)
    raw_id_fields = ("user",)
    autocomplete_fields = ("status", "payment", "delivery_method")
    readonly_fields = ("order_date", "calculated_total_amount")
    inlines = [OrderItemInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', ('order_date', 'status'), 'calculated_total_amount')
        }),
        ('Детали Доставки и Оплаты', {
            'fields': ('delivery_address', 'contact_phone', 'payment', 'delivery_method')
        }),
    )

    @admin.display(description="Пользователь", ordering='user__username')
    def user_link(self, obj):

        if obj.user_id:
            try:
                link = reverse("admin:store_user_change", args=[obj.user_id])
                display_name = obj.user.get_full_name() or obj.user.username
                return format_html('<a href="{}">{}</a>', link, display_name)
            except User.DoesNotExist:
                return "Пользователь удален"
        return "-"

    @admin.display(description="Дата заказа", ordering='order_date')
    def order_date_formatted(self, obj):

        if not obj.order_date: return "-"
        local_time = timezone.localtime(obj.order_date)
        return local_time.strftime('%d.%m.%Y %H:%M')

    @admin.display(description="Сумма заказа")
    def calculated_total_amount(self, obj):
        """Рассчитывает и форматирует сумму заказа для отображения."""

        total = Decimal('0.00')
        items_qs = obj.items.all() if hasattr(obj, 'items') else []
        for item in items_qs:
            try:
                quantity = item.qty if getattr(item, 'qty', None) is not None else 0
                price = item.price_per_item if item.price_per_item is not None else Decimal('0.00')
                total += Decimal(quantity) * Decimal(price)
            except (TypeError, InvalidOperation, AttributeError):
                print(
                    f"Warning: Could not calculate price for item {getattr(item, 'id', 'N/A')} in OrderAdmin for order {obj.id}")
                continue
        return f"{total:.2f} ₽"

    calculated_total_amount.admin_order_field = None

    @admin.action(description='Экспорт активных заказов в PDF (WeasyPrint)')
    def export_active_orders_to_pdf_weasyprint(self, request, queryset):
        """
        Генерирует PDF документ со списком выбранных 'активных' заказов, используя WeasyPrint.
        'Активные' - это заказы НЕ со статусом 'Доставлен' или 'Отменен'.
        """
        if not WEASYPRINT_INSTALLED:
            self.message_user(request, "Ошибка: Библиотека WeasyPrint не установлена или ее зависимости отсутствуют.",
                              level='error')
            return

        inactive_statuses = ['Доставлен', 'Отменен']

        active_orders_qs = queryset.exclude(
            status__status__in=inactive_statuses
        ).select_related(
            'user', 'status', 'delivery_method', 'payment'
        ).order_by('order_date')

        if not active_orders_qs.exists():
            self.message_user(request, "Нет активных заказов среди выбранных для экспорта.", level='warning')
            return

        order_ids = list(active_orders_qs.values_list('id', flat=True))
        order_items_data = OrderItem.objects.filter(order_id__in=order_ids).select_related('product').values(
            'id', 'order_id', 'product__name', 'qty', 'price_per_item'
        )
        items_by_order = {}
        for item_data in order_items_data:
            order_id = item_data['order_id']
            if order_id not in items_by_order: items_by_order[order_id] = []
            items_by_order[order_id].append(item_data)

        orders_for_pdf = []
        for order in active_orders_qs:
            calculated_total = Decimal('0.00')
            items_list_for_pdf = []
            current_order_items = items_by_order.get(order.id, [])
            for item_data in current_order_items:
                try:
                    quantity = item_data.get('qty') or 0
                    price = item_data.get('price_per_item') or Decimal('0.00')
                    price_decimal = Decimal(price)
                    calculated_total += Decimal(quantity) * price_decimal
                    items_list_for_pdf.append({
                        'name': item_data.get('product__name') or 'Товар не найден',
                        'qty': quantity,
                        'price_per_item': price_decimal
                    })
                except (TypeError, InvalidOperation, AttributeError) as e:
                    print(f"Warning: Could not process OrderItem data {item_data.get('id')} for PDF: {e}")
                    items_list_for_pdf.append({'name': f'Ошибка позиции ID {item_data.get("id")}', 'qty': '?',
                                               'price_per_item': Decimal('0.00')})
                    continue
            orders_for_pdf.append({
                'id': order.id,
                'order_date': order.order_date,
                'user': order.user,
                'status': order.status,
                'delivery_method': order.delivery_method,
                'payment': order.payment,
                'calculated_total_amount': calculated_total,
                'items_list': items_list_for_pdf
            })

        context = {
            'orders': orders_for_pdf,
            'generation_date': timezone.now(),
            'STATIC_URL': settings.STATIC_URL,
        }

        try:

            html_string = render_to_string('admin/orders/order_pdf.html', context)

            base_url = path2url(str(settings.BASE_DIR)) + "/"

            html = HTML(string=html_string, base_url=base_url)

            pdf_buffer = io.BytesIO()
            html.write_pdf(target=pdf_buffer)
            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()

        except Exception as e:
            import traceback
            self.message_user(request, f"Ошибка при генерации PDF (WeasyPrint): {e}", level='error')
            print(f"WeasyPrint PDF Generation Error: {e}")
            print(traceback.format_exc())
            return

        if pdf_bytes:
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            response['Content-Disposition'] = f'attachment; filename="active_orders_{timestamp}.pdf"'
            self.message_user(request, f"Экспортировано {len(orders_for_pdf)} активных заказов в PDF.")
            return response
        else:

            return


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order_link", "product_link", "qty", "price_per_item", "total_item_price")
    list_filter = ("product",)
    search_fields = ("product__name", "order__id", "order__user__username")
    list_display_links = None
    raw_id_fields = ("order", "product")
    readonly_fields = ('total_item_price',)

    @admin.display(description="Заказ", ordering='order__id')
    def order_link(self, obj):
        if obj.order_id:
            link = reverse("admin:store_order_change", args=[obj.order_id])
            return format_html('<a href="{}">Заказ #{}</a>', link, obj.order.id)
        return "N/A"

    @admin.display(description="Товар", ordering='product__name')
    def product_link(self, obj):
        if obj.product_id:
            link = reverse("admin:store_product_change", args=[obj.product_id])
            return format_html('<a href="{}">{}</a>', link, obj.product.name)
        return "N/A"

    @admin.display(description="Сумма", ordering='price_per_item')
    def total_item_price(self, obj):
        return obj.total_item_price


class BannerTargetInline(admin.TabularInline):
    model = BannerTarget
    extra = 1


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "position", "start_date", "end_date", "is_active", "is_currently_active")
    list_filter = ("position", "is_active", "start_date", "end_date")
    search_fields = ("title",)
    date_hierarchy = "start_date"
    list_display_links = ("title",)
    readonly_fields = ("created_at", "updated_at", "is_currently_active")
    inlines = [BannerTargetInline]
    fieldsets = (
        (None, {'fields': ('title', 'link_url', 'image', 'position', 'sort_order')}),
        ('Период активности', {'fields': ('start_date', 'end_date', 'is_active', 'is_currently_active')}),
        ('Даты', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description="Активен сейчас?", boolean=True, ordering='start_date')
    def is_currently_active(self, obj):
        return obj.is_currently_active

    is_currently_active.short_description = 'Активен сейчас?'


class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 0
    readonly_fields = ('image_preview', 'uploaded_at')
    fields = ('image', 'image_preview', 'uploaded_at')

    @admin.display(description="Предпросмотр")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<a href="{0}" target="_blank"><img src="{0}" style="max-height: 80px; max-width: 100px;" /></a>',
                obj.image.url)
        return "Нет изображения"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'product_link', 'user_link', 'rating', 'created_at_formatted', 'is_approved', 'display_images', 'short_text')
    list_filter = ('is_approved', 'rating', 'created_at', 'product')
    search_fields = ('user__username', 'product__name', 'text')
    list_editable = ('is_approved',)
    actions = ['approve_selected_reviews', 'unapprove_selected_reviews']
    readonly_fields = ('created_at', 'updated_at')
    list_display_links = None
    autocomplete_fields = ('product', 'user')
    inlines = [ReviewImageInline]
    fieldsets = (
        (None, {'fields': ('product', 'user', 'rating', 'is_approved')}),
        ('Текст отзыва', {'fields': ('text',)}),
        ('Даты', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    list_select_related = ('product', 'user')

    def get_queryset(self, request):

        return super().get_queryset(request).prefetch_related('images')

    @admin.display(description="Прикрепленные фото")
    def display_images(self, obj: Review) -> str:
        """
        Отображает миниатюры прикрепленных к отзыву изображений.
        """

        images = obj.images.all()
        if not images:
            return "Нет фото"

        image_html_parts = []
        for review_image in images:
            if review_image.image and hasattr(review_image.image, 'url'):
                image_html_parts.append(
                    f'<a href="{review_image.image.url}" target="_blank">'
                    f'<img src="{review_image.image.url}" style="max-height: 60px; max-width: 60px; margin-right: 5px; border: 1px solid #ddd; border-radius: 4px;" />'
                    f'</a>'
                )

        if not image_html_parts:
            return "Файлы не найдены"

        return format_html(''.join(image_html_parts))

    @admin.display(description="Товар", ordering='product__name')
    def product_link(self, obj: Review) -> str:
        if obj.product_id:
            link = reverse("admin:store_product_change", args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', link, obj.product.name)
        return "N/A"

    @admin.display(description="Пользователь", ordering='user__username')
    def user_link(self, obj: Review) -> str:
        if obj.user_id:
            link = reverse("admin:store_user_change", args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', link, obj.user.username)
        return "N/A"

    @admin.display(description="Текст (кратко)")
    def short_text(self, obj: Review) -> str:
        return obj.text[:60] + '...' if len(obj.text) > 60 else obj.text

    @admin.display(description="Дата создания", ordering='created_at')
    def created_at_formatted(self, obj: Review) -> str:
        if not obj.created_at: return "-"
        return timezone.localtime(obj.created_at).strftime('%d.%m.%Y %H:%M')

    @admin.action(description='Одобрить выбранные отзывы')
    def approve_selected_reviews(self, request, queryset) -> None:
        updated_count = queryset.update(is_approved=True)
        self.message_user(request, f"{updated_count} отзывов были одобрены.")

    @admin.action(description='Снять одобрение с выбранных отзывов')
    def unapprove_selected_reviews(self, request, queryset) -> None:
        updated_count = queryset.update(is_approved=False)
        self.message_user(request, f"С {updated_count} отзывов было снято одобрение.")


@admin.register(BannerTarget)
class BannerTargetAdmin(admin.ModelAdmin):
    list_display = ("banner", "target_type", "target_id", "get_target_name")
    list_filter = ("target_type",)
    search_fields = ("banner__title", "target_id")
    list_display_links = ("banner",)
    raw_id_fields = ("banner",)

    @admin.display(description="Название цели")
    def get_target_name(self, obj):
        target = obj.get_target()
        if target:

            try:
                app_label = target._meta.app_label
                model_name = target._meta.model_name
                admin_url = reverse(f'admin:{app_label}_{model_name}_change', args=[target.id])
                return format_html('<a href="{}">{}</a>', admin_url, str(target))
            except Exception:
                return str(target)
        return f"Цель не найдена (Тип: {obj.get_target_type_display()}, ID: {obj.target_id})"


class PromotionalProductInline(admin.TabularInline):
    model = PromotionalProduct
    extra = 1
    raw_id_fields = ('product',)
    readonly_fields = ('effective_price',)
    fields = ('product', 'promotional_price', 'effective_price', 'is_featured')

    @admin.display(description="Цена по акции")
    def effective_price(self, obj):
        price = obj.effective_price
        return price if price is not None else "N/A"


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = (
        "name", "discount_type", "discount_value", "start_date", "end_date", "is_active", "is_currently_active")
    list_filter = ("discount_type", "is_active", "start_date", "end_date")
    search_fields = ("name",)
    date_hierarchy = "start_date"
    list_display_links = ("name",)
    readonly_fields = ("created_at", "updated_at", "is_currently_active")
    inlines = [PromotionalProductInline]
    fieldsets = (
        (None, {'fields': ('name', 'description')}),
        ('Условия скидки', {'fields': ('discount_type', 'discount_value')}),
        ('Период действия', {'fields': ('start_date', 'end_date', 'is_active', 'is_currently_active')}),
        ('Даты', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description="Активна сейчас?", boolean=True)
    def is_currently_active(self, obj):
        return obj.is_currently_active


@admin.register(PromotionalProduct)
class PromotionalProductAdmin(admin.ModelAdmin):
    list_display = (
        "product_link", "promotion_link", "effective_price", "base_price", "get_discount_display", "is_featured")
    list_filter = ("promotion", "is_featured")
    search_fields = ("product__name", "promotion__name")
    list_display_links = None
    raw_id_fields = ("product", "promotion")
    readonly_fields = ('effective_price', 'base_price', 'get_discount_display')

    @admin.display(description="Товар", ordering='product__name')
    def product_link(self, obj):
        if obj.product_id:
            link = reverse("admin:store_product_change", args=[obj.product_id])
            return format_html('<a href="{}">{}</a>', link, obj.product.name)
        return "N/A"

    @admin.display(description="Акция", ordering='promotion__name')
    def promotion_link(self, obj):
        if obj.promotion_id:
            link = reverse("admin:store_promotion_change", args=[obj.promotion_id])
            return format_html('<a href="{}">{}</a>', link, obj.promotion.name)
        return "N/A"

    @admin.display(description="Цена акционная", ordering='promotional_price')
    def effective_price(self, obj):
        price = obj.effective_price
        return price if price is not None else "N/A"

    @admin.display(description="Цена базовая")
    def base_price(self, obj):
        return obj.product.price if obj.product else "N/A"

    @admin.display(description="Скидка")
    def get_discount_display(self, obj):
        promo = obj.promotion
        base = self.base_price(obj)
        effective = obj.effective_price
        if promo and base != "N/A" and effective != "N/A" and base > 0:
            if promo.discount_type == 'percentage':
                return f"{promo.discount_value}%"
            elif promo.discount_type == 'fixed':
                return f"{promo.discount_value} руб."
            elif promo.discount_type == 'special_price':
                discount_percent = (1 - (effective / base)) * 100
                return f"Спец.цена ({discount_percent:.1f}%)"
        return "N/A"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'product_link', 'quantity', 'current_price_per_item', 'total_price', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'product__name')
    list_display_links = None
    raw_id_fields = ('user', 'product')
    readonly_fields = ('added_at', 'current_price_per_item', 'total_price')
    list_editable = ('quantity',)

    @admin.display(description="Пользователь", ordering='user__username')
    def user_link(self, obj):
        if obj.user_id:
            link = reverse("admin:store_user_change", args=[obj.user_id])
            return format_html('<a href="{}">{}</a>', link, obj.user.username)
        return "N/A"

    @admin.display(description="Товар", ordering='product__name')
    def product_link(self, obj):
        if obj.product_id:
            link = reverse("admin:store_product_change", args=[obj.product_id])
            return format_html('<a href="{}">{}</a>', link, obj.product.name)
        return "N/A"

    @admin.display(description="Цена за шт. (тек.)")
    def current_price_per_item(self, obj):
        return obj.current_price_per_item

    @admin.display(description="Общая стоимость")
    def total_price(self, obj):
        return obj.total_price


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'product_link', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'product__name')
    list_display_links = None
    raw_id_fields = ('user', 'product')
    readonly_fields = ('added_at',)

    @admin.display(description="Пользователь", ordering='user__username')
    def user_link(self, obj):
        if obj.user_id:
            link = reverse("admin:store_user_change", args=[obj.user_id])
            return format_html('<a href="{}">{}</a>', link, obj.user.username)
        return "N/A"

    @admin.display(description="Товар", ordering='product__name')
    def product_link(self, obj):
        if obj.product_id:
            link = reverse("admin:store_product_change", args=[obj.product_id])
            return format_html('<a href="{}">{}</a>', link, obj.product.name)
        return "N/A"
