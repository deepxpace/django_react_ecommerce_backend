from django.shortcuts import redirect
from django.conf import settings
from django.template.loader import render_to_string

from mailersend import emails

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from userauths.models import User

from store.models import Category, Product, Gallery, Specification, Size, Color, Cart, CartOrder, CartOrderItem, ProductFaq, Review, Wishlist, Notification, Coupon, Tax
from store.serializers import ProductSerializer, CategorySerializer, CartSerializer, CartOrderSerializer, CartOrderItemSerializer, CouponSerializer, NotificationSerializer, ReviewSerializer, WishlistSerializer

# Create your views here.

class OrdersAPIView(generics.ListAPIView):
  serializer_class = CartOrderSerializer
  permission_classes = [AllowAny,]
  
  def get_queryset(self):
    user_id = self.kwargs['user_id']
    
    # Handle case where user_id is undefined or invalid
    if user_id == 'undefined' or not user_id:
      if self.request.user.is_authenticated:
        # Use the authenticated user instead
        user = self.request.user
      else:
        # Return empty queryset if no valid user
        return CartOrder.objects.none()
    else:
      try:
        user = User.objects.get(id=user_id)
      except (User.DoesNotExist, ValueError):
        # Return empty queryset if user doesn't exist or ID is invalid
        return CartOrder.objects.none()
    
    # Show all orders regardless of payment status
    orders = CartOrder.objects.filter(buyer=user)
    return orders
  
class OrderDetailAPIView(generics.RetrieveAPIView):
  serializer_class = CartOrderSerializer
  permission_classes = [AllowAny,]
  
  def get_object(self):
    user_id = self.kwargs['user_id']
    order_oid = self.kwargs['order_oid']
    
    # Handle case where user_id is undefined, "current", or invalid
    if user_id in ['undefined', 'null', 'current'] or not user_id:
      if self.request.user.is_authenticated:
        # Use the authenticated user instead
        user = self.request.user
      else:
        # Return 404 if no valid user
        from django.http import Http404
        raise Http404("User not found - please log in")
    else:
      try:
        user = User.objects.get(id=user_id)
      except (User.DoesNotExist, ValueError):
        from django.http import Http404
        raise Http404("User not found")
    
    try:
      # First try to get order associated with this user
      order = CartOrder.objects.get(buyer=user, oid=order_oid)
      return order
    except CartOrder.DoesNotExist:
      try:
        # If not found by user, try to find the order by just OID (for guest orders)
        order = CartOrder.objects.get(oid=order_oid)
        # If the current user is authenticated and the order has no buyer, associate it
        if self.request.user.is_authenticated and not order.buyer:
          order.buyer = self.request.user
          order.save()
        return order
      except CartOrder.DoesNotExist:
        from django.http import Http404
        raise Http404("Order not found")
  
class WishlistAPIVIew(generics.ListCreateAPIView):
  serializer_class = WishlistSerializer
  permission_classes = [AllowAny,]
  
  def get_queryset(self):
    user_id = self.kwargs['user_id']
    
    user = User.objects.get(id=user_id)
    wishlists = Wishlist.objects.filter(user=user)
    
    return wishlists
  
  def create(self, request, *args, **kwargs):
    payload = request.data
    
    product_id = payload['product_id']
    user_id = payload['user_id']
    
    product = Product.objects.get(id=product_id)
    user = User.objects.get(id=user_id)
    
    wishlist = Wishlist.objects.filter(product=product, user=user)
    
    if wishlist:
      wishlist.delete()
      return Response({'message': 'Removed from wishlist'}, status=status.HTTP_200_OK)
    else:
      Wishlist.objects.create(product=product, user=user)
      return Response({'message': 'Added to wishlist'}, status=status.HTTP_201_CREATED)
    
class CustomerNotification(generics.ListAPIView):
  serializer_class = NotificationSerializer
  permission_classes = [AllowAny,]
  
  def get_queryset(self):
    user_id = self.kwargs['user_id']
    
    user = User.objects.get(id=user_id)
    
    return Notification.objects.filter(user=user, seen=False)
  
class MarkCustomerNotificationAsSeen(generics.RetrieveAPIView):
  serializer_class = NotificationSerializer
  permission_classes = [AllowAny,]
  
  def get_object(self):
    user_id = self.kwargs['user_id']
    noti_id = self.kwargs['noti_id']
    
    user = User.objects.get(id=user_id)
    noti = Notification.objects.get(id=noti_id, user=user)
    
    if noti.seen != True:
      noti.seen = True
      noti.save()    
  
    return noti