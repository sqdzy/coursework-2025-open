import random
import uuid
from decimal import Decimal
from typing import List, Any, Optional, Type

from django.db.models import OuterRef, Subquery, DecimalField, Case, When, F, QuerySet
from django.db.models.functions import Coalesce
from rest_framework.permissions import IsAuthenticated
from social_core.exceptions import AuthException
from social_django.utils import load_strategy, load_backend

from .tasks import send_order_confirmation_email
from django.contrib.auth import get_user_model, authenticate
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from .serializers import LoginOrRegisterSerializer, CartItemSerializer, OrderSerializer, OrderCreateSerializer, \
    DeliveryMethodSerializer, PaymentMethodSerializer, BannerSerializer, CategorySerializer, CategoryDetailSerializer, \
    ReviewSerializer, CustomUserDetailsSerializer
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
from rest_framework import serializers as rest_serializers
from . import serializers


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешение позволяет редактировать объект только его владельцу (по полю 'user').
    Чтение разрешено всем.
    """

    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        """
        Проверяет, что метод SAFE (GET, HEAD, OPTIONS) доступен всем,
        а изменение допустимо только владельцу объекта.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        return hasattr(obj, 'user') and obj.user == request.user


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Просмотр зарегистрированных пользователей (только админ).
    """

    queryset: QuerySet = User.objects.all().order_by('-date_joined')
    serializer_class = serializers.UserSerializer
    permission_classes: List[Any] = [permissions.IsAdminUser]


class OrderStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Просмотр доступных статусов заказа.
    """

    queryset: QuerySet = OrderStatus.objects.all()
    serializer_class = serializers.OrderStatusSerializer
    permission_classes: List[Any] = [permissions.AllowAny]


class BrandViewSet(viewsets.ModelViewSet):
    """
    CRUD для брендов (авторизованный доступ для записи).
    """

    queryset: QuerySet = Brand.objects.all().order_by('name')
    serializer_class = serializers.BrandSerializer
    permission_classes: List[Any] = [permissions.IsAuthenticatedOrReadOnly]


class FeatureViewSet(viewsets.ModelViewSet):
    """
    CRUD для характеристик товаров (только админ).
    """

    queryset: QuerySet = Feature.objects.all().order_by('name')
    serializer_class = serializers.FeatureSerializer
    permission_classes: List[Any] = [permissions.IsAdminUser]


class ReviewViewSet(viewsets.ModelViewSet):
    """
    CRUD для отзывов с поддержкой изображений (с ограничением для обновления).
    """

    serializer_class = ReviewSerializer
    authentication_classes: List[Any] = [TokenAuthentication]
    permission_classes: List[Any] = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self) -> QuerySet:
        """
        Возвращает queryset отзывов. При параметре product_id — фильтрует по товару.
        Только одобренные при list.
        """
        queryset = Review.objects.select_related('user', 'product').prefetch_related('images')
        product_id: Optional[str] = self.request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if self.action == 'list':
            queryset = queryset.filter(is_approved=True)
        return queryset.order_by('-created_at')

    def _handle_uploaded_images(self, review_instance: Review, is_update: bool) -> None:
        """
        Обрабатывает прикреплённые изображения:
        - при создании — добавляет до 2 штук;
        - при обновлении — удаляет указанные и доба
вляет новые до лимита.
        """
        uploaded: List[Any] = self.request.FILES.getlist('uploaded_images')
        if is_update:
            delete_ids: List[str] = self.request.data.getlist('delete_images_ids')
            if delete_ids:
                try:
                    valid_ids = [int(i) for i in delete_ids]
                    review_instance.images.filter(id__in=valid_ids, review=review_instance).delete()
                except ValueError:
                    pass
        max_images = 2
        existing = review_instance.images.count()
        added = 0
        for img in uploaded:
            if existing + added >= max_images:
                break
            ReviewImage.objects.create(review=review_instance, image=img)
            added += 1

    @transaction.atomic
    def create(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        Создание нового отзыва с изображениями.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save(user=request.user)
        self._handle_uploaded_images(review, is_update=False)
        inst = self.get_queryset().get(pk=review.pk)
        resp_ser = self.get_serializer(inst)
        headers = self.get_success_headers(resp_ser.data)
        return Response(resp_ser.data, status=status.HTTP_201_CREATED, headers=headers)

    @transaction.atomic
    def update(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        Обновление отзыва с возможностью удаления/добавления изображений.
        """
        partial: bool = kwargs.pop('partial', False)
        instance: Review = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        self._handle_uploaded_images(review, is_update=True)
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        inst = self.get_queryset().get(pk=instance.pk)
        resp_ser = self.get_serializer(inst)
        return Response(resp_ser.data)


class ProductViewSet(viewsets.ModelViewSet):
    """
    CRUD для товаров с поиск-подсказками и аннотацией актуальной цены.
    """

    permission_classes: List[Any] = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends: List[Any] = [
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend
    ]
    search_fields: List[str] = ['name', 'brand__name', 'category__name']
    ordering_fields: List[str] = ['name', 'price', 'created_at', 'average_rating']
    filterset_fields: List[str] = ['category', 'brand']

    def get_queryset(self) -> QuerySet:
        """
        Базовый queryset с аннотацией actual_price,
        учитывающей текущие акции.
        """
        now = timezone.now()
        active = PromotionalProduct.objects.filter(
            product_id=OuterRef('pk'),
            promotion__is_active=True,
            promotion__start_date__lte=now,
            promotion__end_date__gte=now
        ).order_by('promotional_price').values('promotional_price')[:1]

        queryset = Product.objects.annotate(
            current_promotional_price=Subquery(active, output_field=DecimalField(max_digits=12, decimal_places=2)),
            actual_price=Coalesce(
                Case(
                    When(current_promotional_price__isnull=False,
                         current_promotional_price__lt=F('price'),
                         then=F('current_promotional_price')),
                    default=F('price'),
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                ),
                F('price'),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        ).select_related('category', 'brand') \
            .prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.filter(main_image=True), to_attr='main_image_list'),
            Prefetch('feature_values',
                     queryset=ProductFeatureValue.objects.select_related('feature').order_by('feature__name'))
        ).order_by('-created_at')
        return queryset

    def get_serializer_class(self) -> Any:
        """
        Выбор сериализатора: список или детализация.
        """
        if self.action in ['list', 'search_suggestions']:
            return ProductListSerializer
        return ProductSerializer

    @action(detail=False, methods=['get'], url_path='search-suggestions')
    def search_suggestions(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        Возвращает до 10 товаров для подсказок при поиске.
        """
        qs = self.filter_queryset(self.get_queryset())[:10]
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def list(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        Переопределённый list: пагинация + сериализация.
        """
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)


class ProductImageViewSet(viewsets.ModelViewSet):
    """
    CRUD для изображений товаров (только админ).
    """

    queryset: QuerySet = ProductImage.objects.all()
    serializer_class = serializers.ProductImageSerializer
    permission_classes: List[Any] = [permissions.IsAdminUser]


class ProductFeatureValueViewSet(viewsets.ModelViewSet):
    """
    CRUD для значений характеристик продуктов (только админ).
    """

    queryset: QuerySet = ProductFeatureValue.objects.all().select_related('product', 'feature')
    serializer_class: serializers.ProductFeatureValueSerializer
    permission_classes: List[Any] = [permissions.IsAdminUser]


class OrderViewSet(viewsets.ModelViewSet):
    """
    CRUD для заказов. Только авторизованные пользователи. С доступом к create/create with cart collision.
    """

    permission_classes: List[Any] = [permissions.IsAuthenticated]

    def get_serializer_class(self) -> Any:
        """
        Использует OrderCreateSerializer для создания, иначе - OrderSerializer.
        """
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self) -> QuerySet:
        """
        Возвращает queryset заказов:
        - для админа: все
        - для юзера: только свои
        """
        user = self.request.user
        if not user or not user.is_authenticated:
            return Order.objects.none()
        base = Order.objects.select_related('user', 'status', 'payment', 'delivery_method') \
            .prefetch_related(Prefetch('items', queryset=OrderItem.objects.select_related('product')))
        if user.is_staff or user.is_superuser:
            return base.all().order_by('-order_date')
        return base.filter(user=user).order_by('-order_date')

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
                order_total_amount = Decimal('0.00')
                for item in cart_items:
                    product = item.product
                    product.refresh_from_db(fields=['stock'])
                    if product.stock < item.quantity:
                        raise rest_serializers.ValidationError(f"Недостаточно товара '{product.name}'...")

                    product.stock -= item.quantity
                    products_to_update.append(product)
                    order_total_amount += item.total_price

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

                order_items_to_create = [OrderItem(order=order, product=item.product, qty=item.quantity,
                                                   price_per_item=item.current_price_per_item) for item in cart_items]
                OrderItem.objects.bulk_create(order_items_to_create)
                Product.objects.bulk_update(products_to_update, ['stock'])
                cart_items.delete()

                transaction.on_commit(
                    lambda: send_order_confirmation_email.delay(order.id, str(order_total_amount))
                )

                final_order = self.get_queryset().get(pk=order.pk)
                read_serializer = OrderSerializer(final_order, context=self.get_serializer_context())
                return Response(read_serializer.data, status=status.HTTP_201_CREATED,
                                headers=self.get_success_headers(read_serializer.data))

        except rest_serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import traceback
            print(f"Error creating order for user {user.id}: {e}")
            print(traceback.format_exc())
            return Response({"detail": "Произошла непредвиденная ошибка при создании заказа."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeliveryMethodViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Просмотр доступных способов доставки.
    """

    queryset: QuerySet = DeliveryMethod.objects.all().order_by('id')
    serializer_class: Type[DeliveryMethodSerializer] = DeliveryMethodSerializer
    permission_classes: List[Any] = [permissions.AllowAny]


class PaymentMethodViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Просмотр доступных способов оплаты.
    """

    queryset: QuerySet = PaymentMethod.objects.all().order_by('id')
    serializer_class: Type[PaymentMethodSerializer] = PaymentMethodSerializer
    permission_classes: List[Any] = [permissions.AllowAny]


class OrderItemViewSet(viewsets.ModelViewSet):
    """
    Просмотр и удаление позиций заказа. Только владелец или админ.
    """

    serializer_class: Type[serializers.OrderItemSerializer] = serializers.OrderItemSerializer
    permission_classes: List[Any] = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    http_method_names: List[str] = ['get', 'head', 'options', 'delete']

    def get_queryset(self) -> QuerySet:
        """
        Возвращает позиции заказа:
        - все для админа
        - только свои для обычного пользователя
        """
        user = self.request.user
        base = OrderItem.objects.select_related('order', 'product')
        if user.is_staff or user.is_superuser:
            return base.all()
        return base.filter(order__user=user)


class BannerViewSet(viewsets.ModelViewSet):
    """
    CRUD для баннеров (только админ).
    """

    queryset: QuerySet = Banner.objects.all().prefetch_related('targets').order_by('-created_at')
    serializer_class: Type[BannerSerializer] = BannerSerializer
    permission_classes: List[Any] = [permissions.IsAdminUser]


class BannerTargetViewSet(viewsets.ModelViewSet):
    """
    CRUD для целей баннеров (только админ).
    """

    queryset: QuerySet = BannerTarget.objects.all().select_related('banner')
    serializer_class: Type[serializers.BannerTargetSerializer] = serializers.BannerTargetSerializer
    permission_classes: List[Any] = [permissions.IsAdminUser]


class PromotionViewSet(viewsets.ModelViewSet):
    """
    CRUD для акций:
    - list/retrieve: только активные акции для всех;
    - остальные действия: только для админа.
    """

    permission_classes: List[Any] = [permissions.IsAdminUser]
    serializer_class: Type[serializers.PromotionSerializer] = serializers.PromotionSerializer

    def get_permissions(self) -> List[Any]:
        """
        Позволяет анонимным GET запросам list и retrieve.
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def get_queryset(self) -> QuerySet:
        """
        Возвращает набор акций:
        - для list/retrieve: только активные в текущих датах
        - для админа: все
        - иначе: пустой QuerySet
        """
        user = self.request.user
        now = timezone.now()
        base = Promotion.objects.all().prefetch_related(
            Prefetch(
                'promo_products',
                queryset=PromotionalProduct.objects.select_related('product', 'product__brand')
                .prefetch_related(
                    Prefetch('product__images',
                             queryset=ProductImage.objects.filter(main_image=True),
                             to_attr='main_image_list')
                )
            )
        ).order_by('-start_date', 'name')

        if self.action in ['list', 'retrieve']:
            return base.filter(is_active=True, start_date__lte=now, end_date__gte=now)
        if user and user.is_staff:
            return base
        return Promotion.objects.none()


class PromotionalProductViewSet(viewsets.ModelViewSet):
    """
    CRUD для продуктов в акциях (только админ).
    """

    queryset: QuerySet = PromotionalProduct.objects.all().select_related('product', 'promotion') \
        .order_by('promotion__name', 'product__name')
    serializer_class: Type[serializers.PromotionalProductSerializer] = serializers.PromotionalProductSerializer
    permission_classes: List[Any] = [permissions.IsAdminUser]


class HomepageDataView(APIView):
    """
    Эндпоинт для данных главной страницы.
    Возвращает случайный баннер, категории, акционные и свежие товары.
    """

    permission_classes: List[Any] = [permissions.AllowAny]

    def get(self, request: Any, format: Optional[str] = None) -> Response:
        """
        GET: собирает и возвращает данные:
        - banner: один активный
        - categories: список категорий
        - promotions: до 10 случайных акционных товаров
        - latest_products: 12 свежих товаров
        """
        now = timezone.now()
        active = PromotionalProduct.objects.filter(
            product_id=OuterRef('pk'),
            promotion__is_active=True,
            promotion__start_date__lte=now,
            promotion__end_date__gte=now
        ).order_by('promotional_price').values('promotional_price')[:1]

        def annotate_product_prices(qs: QuerySet) -> QuerySet:
            return qs.annotate(
                current_promotional_price=Subquery(active, output_field=DecimalField(max_digits=12, decimal_places=2)),
                actual_price=Coalesce(
                    Case(
                        When(current_promotional_price__isnull=False,
                             current_promotional_price__lt=F('price'),
                             then=F('current_promotional_price')),
                        default=F('price'),
                        output_field=DecimalField(max_digits=12, decimal_places=2)
                    ),
                    F('price'),
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                )
            )

        active_banners = Banner.objects.filter(
            is_active=True, start_date__lte=now, end_date__gte=now, position='home_top'
        )
        random_banner = random.choice(list(active_banners)) if active_banners.exists() else None
        banner_ser = BannerSerializer(random_banner, context={'request': request}) if random_banner else None

        categories = Category.objects.all().order_by('name')
        category_ser = CategorySerializer(categories, many=True, context={'request': request})

        promo_base = PromotionalProduct.objects.filter(
            promotion__is_active=True,
            promotion__start_date__lte=now,
            promotion__end_date__gte=now
        ).select_related('promotion')
        promo_ids = list(promo_base.values_list('product_id', flat=True))
        promo_qs = annotate_product_prices(Product.objects.filter(id__in=promo_ids)) \
                       .select_related('category', 'brand') \
                       .prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.filter(main_image=True), to_attr='main_image_list')
        ).order_by('?')[:10]
        promo_ser = ProductListSerializer(promo_qs, many=True, context={'request': request})

        latest_base = Product.objects.all().order_by('-created_at')[:12]
        latest_ids = list(latest_base.values_list('id', flat=True))
        latest_qs = annotate_product_prices(Product.objects.filter(id__in=latest_ids)) \
            .select_related('category', 'brand') \
            .prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.filter(main_image=True), to_attr='main_image_list')
        ).order_by('-created_at')
        latest_ser = ProductListSerializer(latest_qs, many=True, context={'request': request})

        data: dict = {
            'banner': banner_ser.data if banner_ser else None,
            'categories': category_ser.data,
            'promotions': promo_ser.data,
            'latest_products': latest_ser.data,
        }
        return Response(data)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD для категорий.
    retrieve: возвращает товары с аннотированной ценой, поддерживает фильтрацию и сортировку.
    """

    queryset: QuerySet = Category.objects.all().order_by('name')
    permission_classes: List[Any] = [permissions.IsAuthenticatedOrReadOnly]
    product_filter_backends: List[Any] = [filters.OrderingFilter, DjangoFilterBackend]
    product_ordering_fields: List[str] = ['name', 'price', 'created_at', 'average_rating']
    product_filterset_fields: List[str] = ['brand']

    def get_serializer_class(self) -> Any:
        """
        Использует детализированный сериализатор при retrieve, иначе — простой.
        """
        if self.action == 'retrieve':
            return CategoryDetailSerializer
        return CategorySerializer

    def get_queryset(self) -> QuerySet:
        """
        Базовый queryset для категорий.
        При retrieve — prefetch товаров с возможностью фильтрации/сортировки.
        """
        qs = super().get_queryset()
        if self.action == 'retrieve' and 'pk' in self.kwargs:
            products_qs = Product.objects.all()

            def annotate_prices(qs_inner: QuerySet) -> QuerySet:
                now = timezone.now()
                active_sq = PromotionalProduct.objects.filter(
                    product_id=OuterRef('pk'),
                    promotion__is_active=True,
                    promotion__start_date__lte=now,
                    promotion__end_date__gte=now
                ).order_by('promotional_price').values('promotional_price')[:1]
                return qs_inner.annotate(
                    current_promotional_price=Subquery(active_sq,
                                                       output_field=DecimalField(max_digits=12, decimal_places=2)),
                    actual_price=Coalesce(
                        Case(
                            When(current_promotional_price__isnull=False,
                                 current_promotional_price__lt=F('price'),
                                 then=F('current_promotional_price')),
                            default=F('price'),
                            output_field=DecimalField(max_digits=12, decimal_places=2)
                        ),
                        F('price'),
                        output_field=DecimalField(max_digits=12, decimal_places=2)
                    )
                )

            annotated = annotate_prices(products_qs)

            class DummyProductFilterView:
                filter_backends = self.product_filter_backends
                ordering_fields = self.product_ordering_fields
                filterset_fields = self.product_filterset_fields
                request = self.request

                def get_queryset(self_inner) -> QuerySet: return annotated

                format_kwarg = None

            filtered = annotated
            for backend in list(DummyProductFilterView().filter_backends):
                filtered = backend().filter_queryset(self.request, filtered, DummyProductFilterView())
            final_qs = filtered.select_related('brand') \
                .prefetch_related(
                Prefetch('images', queryset=ProductImage.objects.filter(main_image=True), to_attr='main_image_list')
            ).order_by('-created_at')
            qs = qs.prefetch_related(Prefetch('products', queryset=final_qs))
        return qs


User = get_user_model()


class LoginOrRegisterView(APIView):
    """
    Эндпоинт для входа или регистрации пользователя.
    """

    permission_classes: List[Any] = [permissions.AllowAny]
    serializer_class: Type[LoginOrRegisterSerializer] = LoginOrRegisterSerializer

    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        """
        POST: если пользователь существует — аутентифицирует по username/password;
        иначе — регистрирует нового и возвращает токен.
        """
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        username: str = serializer.validated_data['username']
        password: str = serializer.validated_data['password']
        user = None
        token_obj = None
        try:
            existing = User.objects.get(username=username)
            user = authenticate(request=request, username=username, password=password)
            if user:
                token_obj, _ = Token.objects.get_or_create(user=user)
                resp = {'token': token_obj.key, 'user': user}
                resp_ser = self.serializer_class(resp)
                return Response(resp_ser.data, status=status.HTTP_200_OK)
            return Response({"detail": "Неверный пароль."}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            try:
                user = User.objects.create_user(username=username, password=password)
                token_obj = Token.objects.create(user=user)
                resp = {'token': token_obj.key, 'user': user}
                resp_ser = self.serializer_class(resp)
                return Response(resp_ser.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"detail": f"Ошибка при регистрации: {e}"},
                                status=status.HTTP_400_BAD_REQUEST)


class CartItemViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    CRUD для элементов корзины (создание, обновление, удаление, просмотр).
    """

    serializer_class: Type[CartItemSerializer] = CartItemSerializer
    authentication_classes: List[Any] = [TokenAuthentication]
    permission_classes: List[Any] = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        """
        Возвращает корзину текущего пользователя, включая основной образ товара.
        """
        user = self.request.user
        if not user or not user.is_authenticated:
            return CartItem.objects.none()
        return CartItem.objects.filter(user=user) \
            .select_related('product', 'product__brand') \
            .prefetch_related(
            Prefetch('product__images', queryset=ProductImage.objects.filter(main_image=True),
                     to_attr='main_image_list')
        ).order_by('-added_at')

    def perform_create(self, serializer: CartItemSerializer) -> None:
        """
        Добавляет или обновляет позицию в корзине. Проверяет наличие на складе.
        """
        user = self.request.user
        product = serializer.validated_data['product']
        quantity = serializer.validated_data.get('quantity', 1)
        cart_item, created = CartItem.objects.get_or_create(
            user=user,
            product=product,
            defaults={'quantity': 0}
        )
        current_qty = 0 if created else cart_item.quantity
        total_qty = current_qty + quantity
        if product.stock < total_qty:
            raise rest_serializers.ValidationError(
                f"Недостаточно товара '{product.name}' на складе. "
                f"Доступно: {product.stock} шт., в корзине уже: {current_qty} шт."
            )
        cart_item.quantity = total_qty
        cart_item.save()
        serializer.instance = cart_item

    def perform_update(self, serializer: CartItemSerializer) -> None:
        """
        Обновляет количество для позиции корзины. Проверяет наличие на складе.
        """
        product = serializer.instance.product
        new_qty = serializer.validated_data['quantity']
        if product.stock < new_qty:
            raise rest_serializers.ValidationError(
                f"Недостаточно товара '{product.name}' на складе. Доступно: {product.stock} шт."
            )
        serializer.save()


class GoogleLoginView(APIView):
    """
    Эндпоинт для входа через Google с использованием access_token, полученного на фронтенде.
    """
    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        access_token = request.data.get('access_token')
        if not access_token:
            return Response(
                {"detail": "Требуется access_token."},
                status=status.HTTP_400_BAD_REQUEST
            )

        strategy = load_strategy(request)
        backend = load_backend(strategy=strategy, name='google-oauth2', redirect_uri=None)

        try:
            user = backend.do_auth(access_token)

        except AuthException as e:
            return Response({"detail": f"Ошибка аутентификации Google: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Произошла ошибка сервера: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if user and user.is_active:
            token, _ = Token.objects.get_or_create(user=user)
            user_data = CustomUserDetailsSerializer(user, context={'request': request}).data

            return Response({
                'token': token.key,
                'user': user_data
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "Не удалось войти с помощью Google."},
                status=status.HTTP_400_BAD_REQUEST
            )