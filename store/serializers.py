from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import (
    Category, Brand, Product, ProductImage, Feature, ProductFeatureValue,
    OrderStatus, PaymentMethod, DeliveryMethod, Order, OrderItem,
    Banner, BannerTarget, Promotion, PromotionalProduct,
    Review, CartItem, ReviewImage
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'created_at']
        read_only_fields = fields


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'description', 'brand_banner']


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ['id', 'name']


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = ['id', 'status', 'description']


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'method_name', 'description']


class DeliveryMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryMethod
        fields = ['id', 'method_name', 'description']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage

        fields = ['id', 'image', 'main_image']


class ProductFeatureValueSerializer(serializers.ModelSerializer):
    feature_name = serializers.CharField(source='feature.name', read_only=True)

    class Meta:
        model = ProductFeatureValue

        fields = ['id', 'feature', 'feature_name', 'value']
        read_only_fields = ('feature_name',)


class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'image', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    images = ReviewImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False, use_url=False),
        write_only=True,
        required=False,
        max_length=2,
        help_text="Список файлов изображений для загрузки (до 2 шт)."
    )

    class Meta:
        model = Review
        fields = [
            'id', 'user', 'product', 'rating', 'text', 'created_at', 'updated_at',
            'images', 'uploaded_images'
        ]
        read_only_fields = ('id', 'user', 'created_at', 'updated_at', 'images')
        extra_kwargs = {
            'product': {'write_only': True, 'required': True}
        }

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Оценка должна быть от 1 до 5.")
        return value

    def validate_text(self, value):
        if not value.strip():
            raise serializers.ValidationError("Текст отзыва не может быть пустым.")
        if len(value) < 10:
            raise serializers.ValidationError("Текст отзыва слишком короткий (минимум 10 символов).")
        return value

    def validate(self, data):
        request = self.context.get('request')
        user = request.user if request and hasattr(request, 'user') else None

        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Необходима аутентификация.")

        if request and request.method == 'POST' and not self.instance:
            product = data.get('product')
            if not product:
                raise serializers.ValidationError({"product": "Необходимо указать товар."})
            if Review.objects.filter(product=product, user=user).exists():
                raise serializers.ValidationError(
                    {"non_field_errors": ["Вы уже оставили отзыв на этот товар."]}
                )
        return data

    def create(self, validated_data):
        validated_data.pop('uploaded_images', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('uploaded_images', None)

        return super().update(instance, validated_data)


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    features = ProductFeatureValueSerializer(source='feature_values', many=True, read_only=True)
    average_rating = serializers.FloatField(source='get_average_rating', read_only=True)
    review_count = serializers.IntegerField(source='get_review_count', read_only=True)

    base_price = serializers.DecimalField(source='price', max_digits=12, decimal_places=2, read_only=True)
    promotional_price = serializers.DecimalField(source='current_promotional_price', max_digits=12, decimal_places=2,
                                                 read_only=True, required=False, allow_null=True)
    price = serializers.DecimalField(source='actual_price', max_digits=12, decimal_places=2, read_only=True)

    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), source='category',
                                                     write_only=True, label="Category ID")
    brand_id = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all(), source='brand', write_only=True,
                                                  label="Brand ID")

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'base_price', 'promotional_price',
            'category', 'category_id', 'brand', 'brand_id', 'created_at',
            'images', 'features', 'average_rating', 'review_count',
        ]

        read_only_fields = ['id', 'created_at', 'images', 'features', 'average_rating', 'review_count', 'price',
                            'base_price', 'promotional_price']

    def get_average_rating(self, obj):
        return obj.get_average_rating()

    def get_review_count(self, obj):
        return obj.get_review_count()


class ProductListSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    brand = serializers.StringRelatedField()
    main_image = serializers.SerializerMethodField()
    average_rating = serializers.FloatField(source='get_average_rating', read_only=True)
    review_count = serializers.IntegerField(source='get_review_count', read_only=True)
    base_price = serializers.DecimalField(source='price', max_digits=12, decimal_places=2, read_only=True)
    promotional_price = serializers.DecimalField(source='current_promotional_price', max_digits=12, decimal_places=2, read_only=True, required=False, allow_null=True)
    price = serializers.DecimalField(source='actual_price', max_digits=12, decimal_places=2, read_only=True)
    stock = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'base_price', 'promotional_price', 'stock',
            'category', 'brand', 'main_image',
            'average_rating', 'review_count', 'created_at'
        ]
        read_only_fields = fields

    def get_main_image(self, obj):
        img_obj = obj.main_image_list[0] if hasattr(obj, 'main_image_list') and obj.main_image_list else None
        if img_obj and img_obj.image:
            request = self.context.get('request')
            return request.build_absolute_uri(img_obj.image.url) if request else img_obj.image.url
        first_img = obj.images.first()
        if first_img and first_img.image:
             request = self.context.get('request')
             return request.build_absolute_uri(first_img.image.url) if request else first_img.image.url
        return None


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'qty', 'price_per_item']


class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    status = OrderStatusSerializer(read_only=True)
    payment = PaymentMethodSerializer(read_only=True)
    delivery_method = DeliveryMethodSerializer(read_only=True)

    status_id = serializers.PrimaryKeyRelatedField(
        queryset=OrderStatus.objects.all(), source='status', write_only=True, label="Order Status ID"
    )
    payment_id = serializers.PrimaryKeyRelatedField(
        queryset=PaymentMethod.objects.all(), source='payment', write_only=True, label="Payment Method ID"
    )
    delivery_method_id = serializers.PrimaryKeyRelatedField(
        queryset=DeliveryMethod.objects.all(), source='delivery_method', write_only=True, label="Delivery Method ID"
    )

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'order_date', 'delivery_address', 'contact_phone',
            'status', 'status_id',
            'payment', 'payment_id',
            'delivery_method', 'delivery_method_id',
            'items'
        ]
        read_only_fields = ['id', 'user', 'order_date', 'items']


class BannerTargetSerializer(serializers.ModelSerializer):
    target_name = serializers.SerializerMethodField()

    class Meta:
        model = BannerTarget
        fields = ['id', 'banner', 'target_type', 'target_id', 'target_name']
        read_only_fields = ['banner', 'target_name']

    def get_target_name(self, obj):
        target = obj.get_target()
        return str(target) if target else "Invalid Target"


class BannerSerializer(serializers.ModelSerializer):
    targets = BannerTargetSerializer(many=True, read_only=True)
    position_display = serializers.CharField(source='get_position_display', read_only=True)

    class Meta:
        model = Banner
        fields = [
            'id', 'title', 'image', 'link_url', 'start_date', 'end_date',
            'position', 'position_display', 'is_active', 'created_at', 'updated_at', 'targets'
        ]
        read_only_fields = ['created_at', 'updated_at', 'targets', 'position_display']


class PromotionalProductSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    promotion = serializers.StringRelatedField(read_only=True)

    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True, label="Product ID"
    )
    promotion_id = serializers.PrimaryKeyRelatedField(
        queryset=Promotion.objects.all(), source='promotion', write_only=True, label="Promotion ID"
    )

    class Meta:
        model = PromotionalProduct
        fields = [
            'id', 'product', 'product_id', 'promotion', 'promotion_id',
            'promotional_price', 'is_featured'
        ]
        read_only_fields = ['id', 'product', 'promotion']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    features = ProductFeatureValueSerializer(source='feature_values', many=True, read_only=True)
    average_rating = serializers.FloatField(source='get_average_rating', read_only=True)
    review_count = serializers.IntegerField(source='get_review_count', read_only=True)
    base_price = serializers.DecimalField(source='price', max_digits=12, decimal_places=2, read_only=True)
    promotional_price = serializers.DecimalField(source='current_promotional_price', max_digits=12, decimal_places=2, read_only=True, required=False, allow_null=True)
    price = serializers.DecimalField(source='actual_price', max_digits=12, decimal_places=2, read_only=True)
    stock = serializers.IntegerField(read_only=True)

    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), source='category', write_only=True, label="Category ID")
    brand_id = serializers.PrimaryKeyRelatedField(queryset=Brand.objects.all(), source='brand', write_only=True, label="Brand ID")

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'base_price', 'promotional_price', 'stock',
            'category', 'category_id', 'brand', 'brand_id', 'created_at',
            'images', 'features', 'average_rating', 'review_count',
        ]
        read_only_fields = ['id', 'created_at', 'images', 'features', 'average_rating', 'review_count', 'price', 'base_price', 'promotional_price', 'stock']


class CategoryDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для детального представления категории,
    включая список товаров в этой категории.
    """

    products = ProductListSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'description',
            'products',
        ]
        read_only_fields = fields


User = get_user_model()


class LoginOrRegisterSerializer(serializers.Serializer):
    """Сериализатор для приема username и password."""
    username = serializers.CharField(max_length=150, write_only=True)
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )

    token = serializers.CharField(read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username_out = serializers.CharField(source='user.username', read_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            raise serializers.ValidationError(
                "Необходимо указать 'username' и 'password'.",
                code='authorization'
            )

        return data


class CartItemSerializer(serializers.ModelSerializer):
    """Сериализатор для позиций корзины."""
    product = ProductListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True, label="ID Товара"
    )

    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    current_price_per_item = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = CartItem
        fields = [
            'id', 'user', 'product', 'product_id', 'quantity', 'added_at',
            'current_price_per_item',
            'total_price',
        ]
        read_only_fields = ('id', 'user', 'product', 'added_at', 'total_price', 'current_price_per_item')

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Количество должно быть не меньше 1.")
        return value

    def update(self, instance, validated_data):
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.save()
        return instance


class OrderCreateSerializer(serializers.Serializer):
    """
    Сериализатор для валидации данных при создании нового заказа.
    Принимает адрес, телефон и ID методов доставки/оплаты.
    """
    delivery_address = serializers.CharField(max_length=500, required=True)
    contact_phone = serializers.CharField(max_length=20, required=True)
    delivery_method_id = serializers.PrimaryKeyRelatedField(
        queryset=DeliveryMethod.objects.all(),
        source='delivery_method',
        write_only=True,
        label="ID Способа доставки"
    )
    payment_method_id = serializers.PrimaryKeyRelatedField(
        queryset=PaymentMethod.objects.all(),
        source='payment_method',
        write_only=True,
        label="ID Способа оплаты"
    )

    def validate_contact_phone(self, value):

        if not value.replace('+', '').replace('(', '').replace(')', '').replace('-', '').replace(' ', '').isdigit():
            raise serializers.ValidationError(
                "Телефон может содержать только цифры, пробелы, скобки, тире и знак плюса.")
        if len(value) < 7:
            raise serializers.ValidationError("Слишком короткий номер телефона.")
        return value

    def validate_delivery_address(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Слишком короткий адрес доставки.")
        return value


class CustomUserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User

        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'created_at', 'last_login')

        read_only_fields = ('id', 'username', 'created_at', 'last_login')

    def validate_email(self, value):

        if User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Этот email уже используется другим пользователем.")
        return value

    def validate_first_name(self, value):
        if len(value) > 0 and len(value) < 2:
            raise serializers.ValidationError("Имя должно содержать минимум 2 символа.")
        return value

    def validate_last_name(self, value):
        if len(value) > 0 and len(value) < 2:
            raise serializers.ValidationError("Фамилия должна содержать минимум 2 символа.")
        return value


class PromotionSerializer(serializers.ModelSerializer):
    """
    Сериализатор для акций. Включает список акционных товаров.
    """
    products = PromotionalProductSerializer(source='promo_products', many=True, read_only=True)
    discount_type_display = serializers.CharField(source='get_discount_type_display', read_only=True)

    class Meta:
        model = Promotion
        fields = [
            'id', 'name', 'description', 'discount_type', 'discount_type_display',
            'discount_value', 'start_date', 'end_date', 'is_active',
            'created_at', 'updated_at', 'products'
        ]
        read_only_fields = ['created_at', 'updated_at', 'products', 'discount_type_display']