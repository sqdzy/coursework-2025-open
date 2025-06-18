from django.urls import path, include
from rest_framework import routers

from . import views

router = routers.DefaultRouter()

router.register(r'users', views.UserViewSet, basename='user')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'brands', views.BrandViewSet, basename='brand')
router.register(r'features', views.FeatureViewSet, basename='feature')
router.register(r'order-statuses', views.OrderStatusViewSet, basename='orderstatus')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'product-images', views.ProductImageViewSet, basename='productimage')
router.register(r'product-features', views.ProductFeatureValueViewSet, basename='productfeaturevalue')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'order-items', views.OrderItemViewSet, basename='orderitem')
router.register(r'banners', views.BannerViewSet, basename='banner')
router.register(r'banner-targets', views.BannerTargetViewSet, basename='bannertarget')
router.register(r'promotions', views.PromotionViewSet, basename='promotion')
router.register(r'promotional-products', views.PromotionalProductViewSet, basename='promotionalproduct')
router.register(r'reviews', views.ReviewViewSet, basename='review')
router.register(r'cart', views.CartItemViewSet, basename='cartitem')
router.register(r'delivery-methods', views.DeliveryMethodViewSet, basename='deliverymethod')
router.register(r'payment-methods', views.PaymentMethodViewSet, basename='paymentmethod')

urlpatterns = [
    path('api/auth/login-or-register/', views.LoginOrRegisterView.as_view(), name='login_or_register'),
    path('api/', include(router.urls)),

    path('api/homepage/', views.HomepageDataView.as_view(), name='homepage-data'),
]
