import random
from django.db.models import OuterRef, Subquery, DecimalField, Case, When, F
from django.db.models.functions import Coalesce
from django.contrib.auth import get_user_model, authenticate
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from .serializers import LoginOrRegisterSerializer, CartItemSerializer, OrderSerializer, OrderCreateSerializer, \
    DeliveryMethodSerializer, PaymentMethodSerializer, BannerSerializer, CategorySerializer, CategoryDetailSerializer, \
    ReviewSerializer
from django.utils import timezone
from rest_framework import status, mixins
from django.db import transaction

from .models import (
    User, Feature, OrderStatus, PaymentMethod,
    DeliveryMethod,
    Order, OrderItem, Banner, BannerTarget, Promotion, PromotionalProduct,
    Review, CartItem, ReviewImage
)
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Prefetch
from .models import Product, ProductImage, Category, Brand, ProductFeatureValue
from .serializers import ProductSerializer, ProductListSerializer
from .utils import annotate_product_prices
from rest_framework import serializers as rest_serializers
from . import serializers


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

                if not cart_items:
                    return Response({"detail": "Ваша корзина пуста."}, status=status.HTTP_400_BAD_REQUEST)

                products_to_update = []
                for item in cart_items:

                    product = item.product
                    product.refresh_from_db(fields=['stock'])

                    if product.stock < item.quantity:
                        raise rest_serializers.ValidationError(
                            f"Недостаточно товара '{product.name}' на складе. Доступно: {product.stock} шт., в заказе: {item.quantity} шт."
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
                headers = self.get_success_headers(read_serializer.data)
                return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


        except rest_serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

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
            raise rest_serializers.ValidationError(
                f"Недостаточно товара '{product.name}' на складе. Доступно: {product.stock} шт., в корзине уже: {current_quantity_in_cart} шт."
            )

        cart_item.quantity += quantity
        cart_item.save()
        serializer.instance = cart_item

    def perform_update(self, serializer):
        product = serializer.instance.product
        new_quantity = serializer.validated_data.get('quantity')

        if product.stock < new_quantity:
            raise rest_serializers.ValidationError(
                f"Недостаточно товара '{product.name}' на складе. Доступно: {product.stock} шт."
            )

        serializer.save()
