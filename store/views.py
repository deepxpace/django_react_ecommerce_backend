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

stripe.api_key = settings.STRIPE_SECRET_KEY

# Create your views here.

def send_notification(user=None, vendor=None, order=None, order_item=None):
  Notification.objects.create(
    user=user,
    vendor=vendor,
    order=order,
    order_item=order_item,
  )

class CategoryListAPIView(generics.ListAPIView):
  queryset = Category.objects.all()
  serializer_class = CategorySerializer
  permission_classes = [AllowAny,]
  
class ProductListAPIView(generics.ListAPIView):
  queryset = Product.objects.all()
  serializer_class = ProductSerializer
  permission_classes = [AllowAny,]
  
class ProductDetailAPIView(generics.RetrieveAPIView):
  serializer_class = ProductSerializer
  permission_classes = [AllowAny,]  
  
  def get_object(self):
    slug = self.kwargs['slug']
    return Product.objects.get(slug=slug)
  
class CartAPIView(generics.ListCreateAPIView):
  queryset = Cart.objects.all()
  serializer_class = CartSerializer
  permission_classes = [AllowAny,]
  
  def create(self, request, *args, **kwargs):
    payload = request.data
    
    product_id = payload['product_id']
    user_id = payload['user_id']
    qty = payload['qty']
    price = payload['price']
    shipping_amount = payload['shipping_amount']
    country = payload['country']
    size = payload['size']
    color = payload['color']
    cart_id = payload['cart_id']
    
    product = Product.objects.get(id=product_id)
    
    # Get the size-specific price
    size_variant = Size.objects.filter(product=product, name=size).first()
    if size_variant:
      price = size_variant.price
    else:
      price = payload['price']  # fallback to default price if no size variant found
    
    if user_id != 'undefined':
      user = User.objects.get(id=user_id)
    else:
      user = None
    
    tax = Tax.objects.filter(country=country).first()
    
    if tax:
      tax_rate = tax.rate / 100
    else:
      tax_rate = 0
      
    cart = Cart.objects.filter(cart_id=cart_id, product=product).first()
    
    if cart:
      cart.product = product
      cart.user = user
      cart.qty = qty
      cart.price = price
      cart.sub_total = Decimal(price) * int(qty)
      cart.shipping_amount = Decimal(shipping_amount) * int(qty)
      cart.tax_fee = int(qty) * Decimal(tax_rate)
      cart.color = color
      cart.size = size
      cart.country = country
      cart.cart_id = cart_id
      
      service_fee_percentage = 5 / 100
      cart.service_fee = Decimal(service_fee_percentage) * cart.sub_total
      
      cart.total = cart.sub_total + cart.shipping_amount + cart.service_fee + cart.tax_fee
      cart.save()
      
      return Response({
        'message': 'Cart updated successfully'
      }, status=status.HTTP_200_OK)
    else:
      cart = Cart()
      
      cart.product = product
      cart.user = user
      cart.qty = qty
      cart.price = price
      cart.sub_total = Decimal(price) * int(qty)
      cart.shipping_amount = Decimal(shipping_amount) * int(qty)
      cart.tax_fee = int(qty) * Decimal(tax_rate)
      cart.color = color
      cart.size = size
      cart.country = country
      cart.cart_id = cart_id
      
      service_fee_percentage = 5 / 100
      cart.service_fee = Decimal(service_fee_percentage) * cart.sub_total
      
      cart.total = cart.sub_total + cart.shipping_amount + cart.service_fee + cart.tax_fee
      cart.save()
      
      return Response({
        'message': 'Cart created successfully'
      }, status=status.HTTP_201_CREATED)
    
class CartListView(generics.ListAPIView):
  serializer_class = CartSerializer
  permission_classes = [AllowAny,]
  queryset = Cart.objects.all()
  
  def get_queryset(self):
    cart_id = self.kwargs['cart_id']
    user_id = self.kwargs.get('user_id')
    
    if user_id is not None:
      user = User.objects.get(id=user_id)
      queryset = Cart.objects.filter(user=user, cart_id=cart_id)
    else:
      queryset = Cart.objects.filter(cart_id=cart_id)
      
    return queryset
  
class CartDetailView(generics.RetrieveAPIView):
  serializer_class = CartSerializer
  permission_classes = [AllowAny,]
  lookup_field = 'cart_id'
  
  def get_queryset(self):
    cart_id = self.kwargs['cart_id']
    user_id = self.kwargs.get('user_id')
    
    if user_id is not None:
      user = User.objects.get(id=user_id)
      queryset = Cart.objects.filter(user=user, cart_id=cart_id)
    else:
      queryset = Cart.objects.filter(cart_id=cart_id)
      
    return queryset
  
  def get(self, request, *args, **kwargs):
    queryset = self.get_queryset()
    
    total_shipping = 0.0
    total_tax = 0.0
    total_service_fee = 0.0
    total_sub_total = 0.0
    total_total = 0.0
    
    for cart_item in queryset:
      total_shipping += float(self.calculate_shipping(cart_item))
      total_tax += float(self.calculate_tax(cart_item))
      total_service_fee += float(self.calculate_service_fee(cart_item))
      total_sub_total += float(self.calculate_sub_total(cart_item))
      total_total += float(self.calculate_total(cart_item))
      
    data = {
      'shipping': total_shipping,
      'tax': total_tax,
      'service_fee': total_service_fee,
      'sub_total': total_sub_total,
      'total': total_total,
    }
    
    return Response(data)
    
  def calculate_shipping(self, cart_item):
    return cart_item.shipping_amount
  
  def calculate_tax(self, cart_item):
    return cart_item.tax_fee
  
  def calculate_service_fee(self, cart_item):
    return cart_item.service_fee
  
  def calculate_sub_total(self, cart_item):
    return cart_item.sub_total
  
  def calculate_total(self, cart_item):
    return cart_item.total
  
class CartItemDeleteAPIView(generics.DestroyAPIView):
  serializer_class = CartSerializer
  lookup_field = 'cart_id'
  
  def get_object(self):
    cart_id = self.kwargs['cart_id']
    item_id = self.kwargs['item_id']
    user_id = self.kwargs.get('user_id')  
    
    if user_id:
      user = User.objects.get(id=user_id)
      cart = Cart.objects.get(id=item_id, cart_id=cart_id, user=user)
    else:
      cart = Cart.objects.get(id=item_id, cart=cart_id)
      
    return cart
  
class CreateOrderAPIView(generics.CreateAPIView):
  serializer_class = CartOrderSerializer
  queryset = CartOrder.objects.all()
  permission_classes = [AllowAny,]
  
  def create(self, request):
    payload = request.data
    
    full_name = payload['full_name']
    email = payload['email']
    mobile = payload['mobile']
    address = payload['address']
    city = payload['city']
    state = payload['state']
    country = payload['country']
    cart_id = payload['cart_id']
    user_id = payload['user_id']
    
    try:
      user = User.objects.get(id=user_id)
    except:
      user = None
      
    cart_items = Cart.objects.filter(cart_id=cart_id)
    
    total_shipping = Decimal(0.00)
    total_tax = Decimal(0.00)
    total_service_fee = Decimal(0.00)
    total_sub_total = Decimal(0.00)
    total_initial_total = Decimal(0.00)
    total_total = Decimal(0.00)
    
    order = CartOrder.objects.create(
      buyer=user,
      full_name=full_name,
      email=email,
      mobile=mobile,
      address=address,
      city=city,
      state=state,
      country=country,
    )
    
    for c in cart_items:
      CartOrderItem.objects.create(
        order=order,
        product=c.product,
        vendor=c.product.vendor,
        qty=c.qty,
        color=c.color,
        size=c.size,
        price=c.price,
        sub_total=c.sub_total,
        shipping_amount=c.shipping_amount,
        service_fee=c.service_fee,
        tax_fee=c.tax_fee,
        total=c.total,
        initial_total=c.total,
      )
      
      total_shipping += Decimal(c.shipping_amount)
      total_tax += Decimal(c.tax_fee)
      total_service_fee += Decimal(c.service_fee)
      total_sub_total += Decimal(c.sub_total)
      total_initial_total += Decimal(c.total)
      total_total += Decimal(c.total)
      
      order.vendor.add(c.product.vendor)
    
    order.sub_total = total_sub_total
    order.shipping_amount = total_shipping
    order.tax_fee = total_tax
    order.service_fee = total_service_fee
    order.initial_total = total_initial_total
    order.total = total_total
    
    order.save()
    
    return Response({
      'message': 'Order Created Successfully', 
      'order_oid':order.oid
    }, status=status.HTTP_201_CREATED)
  
class CheckoutView(generics.RetrieveAPIView):
  serializer_class = CartOrderSerializer
  lookup_field = 'order_oid'
  permission_classes = [AllowAny,]
  
  def get_object(self):
    order_oid = self.kwargs['order_oid']
    order = CartOrder.objects.get(oid=order_oid)
    
    return order
  
class CouponAPIView(generics.CreateAPIView):
  serializer_class = CouponSerializer
  queryset = Coupon.objects.all()
  permission_classes = [AllowAny,]
  
  def create(self, request):
    payload = request.data
    
    order_oid = payload['order_oid']
    coupon_code = payload['coupon_code']
    
    order = CartOrder.objects.get(oid=order_oid)
    coupon = Coupon.objects.filter(code=coupon_code).first()
    
    if coupon:
      order_items = CartOrderItem.objects.filter(order=order, vendor=coupon.vendor)
      
      if order_items:
        for i in order_items:
          if not coupon in i.coupon.all():
            discount = i.total * coupon.discount / 100
            
            i.total -= discount
            i.sub_total -= discount
            i.coupon.add(coupon)
            i.saved += discount
            
            order.total -= discount
            order.sub_total -= discount
            order.saved += discount
            
            i.save()
            order.save()
            
            return Response({
              'message': 'Coupon Successfully Activated', 
              'status': 'success'
            }, status=status.HTTP_200_OK)
          else:
            return Response({
              'message': 'Coupon Already Activated', 
              'status': 'warning'
            }, status=status.HTTP_200_OK)
      else:
        return Response({
          'message': 'Order Item Does not Exists', 
          'status': 'error'
        }, status=status.HTTP_200_OK)
    else:
      return Response({
        'message': 'Coupon Does not Exists', 
        'status': 'error'
      }, status=status.HTTP_200_OK)
    
class StripeCheckoutAPIView(generics.CreateAPIView):
  serializer_class = CartOrderSerializer
  permission_classes = [AllowAny,]
  queryset = CartOrder.objects.all()
  
  def create(self, *args, **kwargs):
    order_oid = self.kwargs['order_oid']
    order = CartOrder.objects.get(oid=order_oid)
    
    if not order:
      return Response({
        'message': 'Order not Found'}, 
        status=status.HTTP_404_NOT_FOUND
      )
    
    try:
      checkout_session = stripe.checkout.Session.create(
        customer_email=order.email,
        payment_method_types=['card'],
        line_items=[
          {
            'price_data': {
              'currency': 'usd',
              'product_data': {
                'name': order.full_name,
              },
              'unit_amount': int(order.total * 100)
            },
            'quantity': 1,
          }
        ],
        mode='payment',
        success_url='http://localhost:5173/payment-success/' + order_oid + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url='http://localhost:5173/payment-failed/?session_id={CHECKOUT_SESSION_ID}'
      )
    
      order.stripe_session_id = checkout_session.id
      order.save()
      
      return redirect(checkout_session.url)
    except stripe.error.StripeError as e:
      return Response({'error': f'Something went wrong while creating checkout session: {str(e)}'})
    
def calculate_vendor_totals(order_items, vendor):
  vendor_items = [item for item in order_items if item.vendor.id == vendor.id]
  sub_total = sum(item.sub_total for item in vendor_items)
  shipping_total = sum(item.shipping_amount for item in vendor_items)
  return {
      'vendor_sub_total': sub_total,
      'vendor_shipping_total': shipping_total,
      'vendor_items': vendor_items
  }    
    
def get_access_token(client_id, secret_id):
  try:
      print("Getting PayPal access token...")
      token_url = 'https://api.sandbox.paypal.com/v1/oauth2/token'
      data = {'grant_type': 'client_credentials'}
      auth = (client_id, secret_id)  # Perbaiki format auth
      print("Making token request to:", token_url)
      
      response = requests.post(token_url, data=data, auth=auth)
      print("Token response status:", response.status_code)
      print("Token response:", response.text)
      
      if response.status_code == 200:
          token = response.json()['access_token']
          print('Got access token:', token[:10] + '...')
          return token
      else:
          raise Exception(f'Failed to get access token: {response.status_code} - {response.text}')
  
  except Exception as e:
      print("Error getting access token:", str(e))
      print(traceback.format_exc())
      raise 

class PaymentSuccessView(generics.CreateAPIView):
  serializer_class = CartOrderSerializer
  permission_classes = [AllowAny,]
  queryset = CartOrder.objects.all()

  def _get_paypal_order_status(self, paypal_order_id):
    """Verify PayPal order status"""
    try:
      print('Verifying PayPal payment...')
      paypal_api_url = f'https://api-m.sandbox.paypal.com/v2/checkout/orders/{paypal_order_id}'
      headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {get_access_token(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET_ID)}'
      }
      
      response = requests.get(paypal_api_url, headers=headers)
      print('PayPal API Response:', response.status_code, response.text)
      
      if response.status_code == 200:
        return response.json().get('status')
      return None
    
    except Exception as e:
        print(f"PayPal verification error: {str(e)}")
        return None

  def _send_vendor_notification(self, vendor, order, order_items):
      """Send email notification to vendor"""
      try:
        context = {
          'order': order,
          'order_items': order_items,
          'vendor': vendor,
          **calculate_vendor_totals(order_items, vendor)
        }
        
        mail_body = {}
        mail_from = {
          "name": "Upfront",
          "email": settings.FROM_EMAIL,
        }
        recipients = [{
          "name": vendor.name,
          "email": vendor.user.email,
        }]
        
        mailer = emails.NewEmail(settings.MAILERSEND_API_KEY)
        mailer.set_mail_from(mail_from, mail_body)
        mailer.set_mail_to(recipients, mail_body)
        mailer.set_subject("New sale!", mail_body)
        mailer.set_html_content(
          render_to_string('email/vendor_sale.html', context),
          mail_body
        )
        
        mailer.send(mail_body)
        
      except Exception as e:
        print(f"Vendor notification error: {traceback.format_exc()}")

  def _send_customer_notification(self, order, order_items):
      """Send email notification to customer"""
      try:
          context = {
              'order': order,
              'order_items': order_items,
          }
          
          mail_body = {}
          mail_from = {
              "name": "Upfront",
              "email": settings.FROM_EMAIL,
          }
          recipients = [{
              "name": order.full_name,
              "email": order.email,
          }]
          
          mailer = emails.NewEmail(settings.MAILERSEND_API_KEY)
          mailer.set_mail_from(mail_from, mail_body)
          mailer.set_mail_to(recipients, mail_body)
          mailer.set_subject("Order placed successfully", mail_body)
          mailer.set_html_content(
              render_to_string('email/customer_order_confirmation.html', context),
              mail_body
          )
          
          mailer.send(mail_body)
      except Exception as e:
          print(f"Customer notification error: {traceback.format_exc()}")

  def _process_successful_payment(self, order, order_items, transaction_id=None):
    """Process successful payment and send notifications"""
    if order.payment_status != 'pending':
        return Response({
            'message': 'Payment has already been processed',
            'status': 'info'
        })

    order.payment_status = 'paid'
    if transaction_id:  # Save the transaction ID
        order.paypal_order_id = transaction_id
    order.save()

    # Send notifications
    if order.buyer:
        send_notification(user=order.buyer, order=order)        
        self._send_customer_notification(order, order_items)

    # Send vendor notifications
    vendors_notified = set()  # Track which vendors have been notified
    for item in order_items:
        if item.vendor.id not in vendors_notified:
            send_notification(vendor=item.vendor, order=order, order_item=item)
            self._send_vendor_notification(item.vendor, order, order_items)
            vendors_notified.add(item.vendor.id)

    return Response({
        'message': 'Payment completed successfully',
        'status': 'success'
    })

  def create(self, request, *args, **kwargs):
    try:
        payload = request.data
        order_oid = payload.get('order_oid')
        session_id = payload.get('session_id')
        paypal_order_id = payload.get('paypal_order_id')
        
        if not order_oid:
            return Response(
                {'message': 'Order ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            order = CartOrder.objects.get(oid=order_oid)
            order_items = CartOrderItem.objects.filter(order=order)
        except CartOrder.DoesNotExist:
            return Response(
                {'message': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # PayPal Payment
        if paypal_order_id and paypal_order_id != 'null':
            paypal_status = self._get_paypal_order_status(paypal_order_id)
            
            if paypal_status == 'COMPLETED':
                return self._process_successful_payment(order, order_items, transaction_id=paypal_order_id)
            elif paypal_status:
                return Response({
                    'message': 'Payment pending. Please complete your payment',
                    'status': 'warning'
                })
        
        # Stripe Payment
        if session_id and session_id != 'null':
            try:
                session = stripe.checkout.Session.retrieve(session_id)
                
                if session.payment_status == 'paid':
                    return self._process_successful_payment(order, order_items)
                elif session.payment_status == 'unpaid':
                    return Response({
                        'message': 'Payment pending. Please complete your payment',
                        'status': 'warning'
                    })
                elif session.payment_status == 'cancelled':
                    return Response({
                        'message': 'Payment cancelled. Please try again or contact support',
                        'status': 'error'
                    })
            except stripe.error.StripeError as e:
                return Response({
                    'message': 'Payment verification failed. Please try again or contact support',
                    'error': str(e),
                    'status': 'error'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'message': 'Invalid payment information provided',
            'status': 'error'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        print(f"Unexpected error: {traceback.format_exc()}")
        return Response({
            'message': 'An unexpected error occurred',
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ReviewListAPIView(generics.ListCreateAPIView):
  serializer_class = ReviewSerializer
  permission_classes = [AllowAny,]
  
  def get_queryset(self):
    product_id = self.kwargs['product_id']
    
    product = Product.objects.get(id=product_id)
    reviews = Review.objects.filter(product=product)
    
    return reviews
  
  def create(self, request, *args, **kwargs):
    payload = request.data
    
    user_id = payload['user_id']
    product_id = payload['product_id']
    rating = payload['rating']
    review = payload['review']
    
    user = User.objects.get(id=user_id)
    product = Product.objects.get(id=product_id)
    
    Review.objects.create(
      user=user,
      product=product,
      rating=rating,
      review=review,
    )
    
    return Response({
      'message': 'Review created successfully',
      'status': 'success'
    }, status=status.HTTP_200_OK)