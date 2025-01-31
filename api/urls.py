from django.urls import path 

from rest_framework_simplejwt.views import TokenRefreshView

from userauths import views as userauths_views
from store import views as store_views

urlpatterns = [
  path('user/token/', userauths_views.MyTokenObtainPairView.as_view()),
  path('user/token/refresh/', TokenRefreshView.as_view()),
  path('user/register/', userauths_views.RegisterView.as_view()),
  path('user/password-reset/<email>/', userauths_views.PasswordResetEmailVerify.as_view()),
  path('user/password-change/', userauths_views.PasswordChangeView.as_view()),
  
  # STORE ENDPOINTS
  path('category/', store_views.CategoryListAPIView.as_view()),
  path('products/', store_views.ProductListAPIView.as_view()),
  path('products/<slug>/', store_views.ProductDetailAPIView.as_view()),
  path('cart-view/', store_views.CartAPIView.as_view()),
  path('cart-list/<str:cart_id>/<int:user_id>/', store_views.CartListView.as_view()),
  path('cart-list/<str:cart_id>/', store_views.CartListView.as_view()),
  path('cart-detail/<str:cart_id>/<int:user_id>/', store_views.CartDetailView.as_view()),
  path('cart-detail/<str:cart_id>/', store_views.CartDetailView.as_view()),
  path('cart-delete/<str:cart_id>/<str:item_id>/<int:user_id>/', store_views.CartItemDeleteAPIView.as_view()),
  path('cart-delete/<str:cart_id>/<str:item_id>/', store_views.CartItemDeleteAPIView.as_view()),
  path('create-order/', store_views.CreateOrderAPIView.as_view()),
  path('checkout/<order_oid>/', store_views.CheckoutView.as_view()),
  path('coupon/', store_views.CouponAPIView.as_view()),
  path('reviews/<product_id>/', store_views.ReviewListAPIView.as_view()),
  path('search/', store_views.SearchProductAPIView.as_view()),
  
  # Payment Endpoints
  path('stripe-checkout/<order_oid>/', store_views.StripeCheckoutAPIView.as_view()),
  path('payment-success/<order_oid>/', store_views.PaymentSuccessView.as_view()),
]
