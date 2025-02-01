from django.shortcuts import redirect
from django.conf import settings
from django.template.loader import render_to_string

from mailersend import emails

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from userauths.models import User

from store.models import Category, Product, Gallery, Specification, Size, Color, Cart, CartOrder, CartOrderItem, ProductFaq, Review, Wishlist, Notification, Coupon, Tax
from store.serializers import ProductSerializer, CategorySerializer, CartSerializer, CartOrderSerializer, CartOrderItemSerializer, CouponSerializer, NotificationSerializer, ReviewSerializer

from decimal import Decimal

import stripe
import stripe.error
import traceback
import requests

# Create your views here.

class OrdersAPIView(generics.ListAPIView):
  serializer_class = CartOrderSerializer
  permission_classes = [AllowAny,]
  
  def get_queryset(self):
    user_id = self.kwargs['user_id']
    user = User.objects.get(id=user_id)
    
    orders = CartOrder.objects.filter(buyer=user, payment_status='paid')
    return orders
  
class OrderDetailAPIView(generics.RetrieveAPIView):
  serializer_class = CartOrderSerializer
  permission_classes = [AllowAny,]
  
  def get_object(self):
    user_id = self.kwargs['user_id']
    order_oid = self.kwargs['order_oid']
    
    user = User.objects.get(id=user_id)
    
    order = CartOrder.objects.get(buyer=user, oid=order_oid, payment_status='paid')
    return order
  
