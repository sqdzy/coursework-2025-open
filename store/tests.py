from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from decimal import Decimal
from django.utils import timezone

from .models import (
    User, Product, Category, Brand, CartItem, Order, OrderItem,
    OrderStatus, DeliveryMethod, PaymentMethod, Review
)


class BaseTestCase(APITestCase):
    """
    Базовый класс, который создает общие объекты для всех тестов.
    Метод setUp будет выполняться перед каждым тестом.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.admin_user = User.objects.create_superuser(username='adminuser', password='password123')

        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        self.category = Category.objects.create(name='Тестовая Категория')
        self.brand = Brand.objects.create(name='Тестовый Бренд')
        self.product = Product.objects.create(
            name='Тестовый Товар',
            price=Decimal('1000.00'),
            category=self.category,
            brand=self.brand,
            stock=10
        )
        self.product_out_of_stock = Product.objects.create(
            name='Товар не в наличии',
            price=Decimal('500.00'),
            category=self.category,
            brand=self.brand,
            stock=0
        )


class ModelTests(BaseTestCase):

    def test_product_str_representation(self):
        """1. Тестирование строкового представления модели Product."""
        self.assertEqual(str(self.product), 'Тестовый Товар')

    def test_order_total_amount_calculation(self):
        """2. Тестирование метода-свойства total_amount в модели Order."""
        order_status = OrderStatus.objects.create(status='Новый')
        order = Order.objects.create(user=self.user, status=order_status)
        OrderItem.objects.create(order=order, product=self.product, qty=2, price_per_item=Decimal('1000.00'))
        OrderItem.objects.create(order=order, product=self.product_out_of_stock, qty=3,
                                 price_per_item=Decimal('500.00'))

        expected_total = Decimal('3500.00')
        self.assertEqual(order.total_amount, expected_total)

    def test_order_creation_with_zero_total_amount(self):
        """3. Тестирование создания заказа с нулевой суммой (без товаров)."""
        order_status = OrderStatus.objects.create(status='Новый')
        order = Order.objects.create(user=self.user, status=order_status)

        self.assertEqual(order.total_amount, Decimal('0.00'))


class APITests(BaseTestCase):

    def test_get_product_list(self):
        """4. Тестирование получения списка товаров (GET /api/products/)."""
        url = reverse('product-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data['results']), 2)

    def test_product_filtering_by_category(self):
        """5. Тестирование фильтрации товаров по категории."""
        new_category = Category.objects.create(name='Другая Категория')
        Product.objects.create(name='Другой товар', price=100, category=new_category, brand=self.brand)

        url = reverse('product-list') + f'?category={self.category.id}'
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data['results']), 2)

        self.assertEqual(response.data['results'][0]['category'], self.category.name)

    def test_add_to_cart_authenticated(self):
        """6. Тестирование добавления товара в корзину авторизованным пользователем."""
        url = reverse('cartitem-list')
        data = {'product_id': self.product.id, 'quantity': 2}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(CartItem.objects.get().quantity, 2)

    def test_add_to_cart_unauthenticated(self):
        """7. Тестирование: неавторизованный пользователь не может добавить в корзину."""
        self.client.credentials()
        url = reverse('cartitem-list')
        data = {'product_id': self.product.id, 'quantity': 1}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_stock_validation_on_cart_add(self):
        """8. Тестирование валидации остатков на складе при добавлении в корзину."""
        url = reverse('cartitem-list')

        data = {'product_id': self.product.id, 'quantity': 11}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("Недостаточно товара", str(response.data))

    def test_create_order_from_cart(self):
        """9. Тестирование создания заказа из корзины."""

        CartItem.objects.create(user=self.user, product=self.product, quantity=3)

        delivery_method = DeliveryMethod.objects.create(method_name='Тест Доставка')
        payment_method = PaymentMethod.objects.create(method_name='Тест Оплата')

        url = reverse('order-list')
        data = {
            "delivery_address": "Тестовый адрес, д. 1, кв. 2",
            "contact_phone": "+79991234567",
            "delivery_method_id": delivery_method.id,
            "payment_method_id": payment_method.id
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()

        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().qty, 3)

        self.assertEqual(CartItem.objects.count(), 0)

    def test_create_order_with_empty_cart(self):
        """10. Тестирование: нельзя создать заказ с пустой корзиной."""
        delivery_method = DeliveryMethod.objects.create(method_name='Тест Доставка')
        payment_method = PaymentMethod.objects.create(method_name='Тест Оплата')

        url = reverse('order-list')
        data = {
            "delivery_address": "Тестовый адрес для проверки",
            "contact_phone": "+71234567890",
            "delivery_method_id": delivery_method.id,
            "payment_method_id": payment_method.id
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Ваша корзина пуста.")

