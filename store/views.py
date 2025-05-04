from django.shortcuts import redirect
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail

from mailersend import emails

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from userauths.models import User

from store.models import (
    Category,
    Product,
    Gallery,
    Specification,
    Size,
    Color,
    Cart,
    CartOrder,
    CartOrderItem,
    ProductFaq,
    Review,
    Wishlist,
    Notification,
    Coupon,
    Tax,
    SiteSettings,
)
from store.serializers import (
    ProductSerializer,
    CategorySerializer,
    CartSerializer,
    CartOrderSerializer,
    CartOrderItemSerializer,
    CouponSerializer,
    NotificationSerializer,
    ReviewSerializer,
)

from decimal import Decimal

import stripe
import stripe.error
import traceback
import requests

stripe.api_key = settings.STRIPE_SECRET_KEY

# Create your views here.


def send_notification(user=None, vendor=None, order=None, order_item=None, type="system"):
    Notification.objects.create(
        user=user,
        vendor=vendor,
        order=order,
        order_item=order_item,
        type=type
    )


class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [
        AllowAny,
    ]


class ProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [
        AllowAny,
    ]


class ProductDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    permission_classes = [
        AllowAny,
    ]

    def get_object(self):
        slug = self.kwargs["slug"]
        return Product.objects.get(slug=slug)


class CartAPIView(generics.ListCreateAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [
        AllowAny,
    ]

    def create(self, request, *args, **kwargs):
        payload = request.data

        product_id = payload["product_id"]
        user_id = payload["user_id"]
        qty = payload["qty"]
        price = payload["price"]
        shipping_amount = payload["shipping_amount"]
        country = payload["country"]
        size = payload["size"]
        color = payload["color"]
        cart_id = payload["cart_id"]

        product = Product.objects.get(id=product_id)

        # Get the size-specific price
        size_variant = Size.objects.filter(product=product, name=size).first()
        if size_variant:
            price = size_variant.price
        else:
            price = payload[
                "price"
            ]  # fallback to default price if no size variant found

        # Better handling of anonymous users
        user = None
        if user_id and user_id not in ("undefined", "null"):
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                user = None

        tax = Tax.objects.filter(country=country).first()

        if tax:
            tax_rate = tax.rate / 100
        else:
            tax_rate = 0

        cart = Cart.objects.filter(cart_id=cart_id, product=product).first()

        if int(qty) == 0:
            if cart:
                cart.delete()
                return Response(
                    {"message": "Item removed from cart"},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": "Item not found in cart"},
                    status=status.HTTP_404_NOT_FOUND,
                )

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

            # Get service fee percentage from site settings
            site_settings = SiteSettings.get_settings()
            service_fee_percentage = Decimal(site_settings.service_fee_percentage) / 100
            cart.service_fee = service_fee_percentage * cart.sub_total

            cart.total = (
                cart.sub_total + cart.shipping_amount + cart.service_fee + cart.tax_fee
            )
            cart.save()

            return Response(
                {"message": "Cart updated successfully"}, status=status.HTTP_200_OK
            )
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

            # Get service fee percentage from site settings
            site_settings = SiteSettings.get_settings()
            service_fee_percentage = Decimal(site_settings.service_fee_percentage) / 100
            cart.service_fee = service_fee_percentage * cart.sub_total

            cart.total = (
                cart.sub_total + cart.shipping_amount + cart.service_fee + cart.tax_fee
            )
            cart.save()

            return Response(
                {"message": "Cart created successfully"}, status=status.HTTP_201_CREATED
            )


class CartListView(generics.ListAPIView):
    serializer_class = CartSerializer
    permission_classes = [
        AllowAny,
    ]
    queryset = Cart.objects.all()

    def get_queryset(self):
        cart_id = self.kwargs["cart_id"]
        user_id = self.kwargs.get("user_id")

        if user_id is not None and user_id not in ('null', 'undefined'):
            try:
                user = User.objects.get(id=user_id)
                queryset = Cart.objects.filter(user=user, cart_id=cart_id)
            except (User.DoesNotExist, ValueError):
                queryset = Cart.objects.filter(cart_id=cart_id)
        else:
            queryset = Cart.objects.filter(cart_id=cart_id)

        return queryset


class CartDetailView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [
        AllowAny,
    ]
    lookup_field = "cart_id"

    def get_queryset(self):
        cart_id = self.kwargs["cart_id"]
        user_id = self.kwargs.get("user_id")

        if user_id is not None and user_id not in ('null', 'undefined'):
            try:
                user = User.objects.get(id=user_id)
                queryset = Cart.objects.filter(user=user, cart_id=cart_id)
            except (User.DoesNotExist, ValueError):
                queryset = Cart.objects.filter(cart_id=cart_id)
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
            "shipping": total_shipping,
            "tax": total_tax,
            "service_fee": total_service_fee,
            "sub_total": total_sub_total,
            "total": total_total,
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
    lookup_field = "cart_id"

    def get_object(self):
        cart_id = self.kwargs["cart_id"]
        item_id = self.kwargs["item_id"]
        user_id = self.kwargs.get("user_id")

        if user_id and user_id not in ('null', 'undefined'):
            try:
                user = User.objects.get(id=user_id)
                cart = Cart.objects.get(id=item_id, cart_id=cart_id, user=user)
            except (User.DoesNotExist, ValueError):
                cart = Cart.objects.get(id=item_id, cart_id=cart_id)
        else:
            cart = Cart.objects.get(id=item_id, cart_id=cart_id)

        return cart


class CreateOrderAPIView(generics.CreateAPIView):
    serializer_class = CartOrderSerializer
    queryset = CartOrder.objects.all()
    permission_classes = [
        AllowAny,
    ]

    def _send_admin_notification(self, order, order_items):
        """Send email notification to admin"""
        try:
            print(f"Attempting to send admin notification for order {order.oid}")
            
            # First, create a database notification for admin users
            try:
                # Find admin users
                admin_users = User.objects.filter(is_superuser=True)
                print(f"Found {admin_users.count()} admin users")
                
                # Create notification for each admin
                for admin in admin_users:
                    notification = Notification.objects.create(
                        user=admin,
                        order=order,
                        seen=False,
                        type="admin"
                    )
                    notification.save()
                    print(f"Created database notification for admin: {admin.email}")
            except Exception as notif_error:
                print(f"Error creating admin database notification: {str(notif_error)}")
            
            # Then continue with email notification
            context = {
                "order": order,
                "order_items": order_items,
                "is_admin_notification": True,
            }

            mail_body = {}
            mail_from = {
                "name": "Koshimart System",
                "email": settings.FROM_EMAIL,
            }
            
            # Admin email - hardcoded to ensure it's correct
            admin_email = "deepxpacelab@gmail.com"
            
            recipients = [
                {
                    "name": "Admin",
                    "email": admin_email,
                }
            ]
            
            print(f"Sending admin notification to {admin_email}")
            print(f"Using FROM_EMAIL: {settings.FROM_EMAIL}")
            print(f"Using MAILERSEND_API_KEY: {settings.MAILERSEND_API_KEY[:5]}...")

            # First try with MailerSend
            try:
                mailer = emails.NewEmail(settings.MAILERSEND_API_KEY)
                mailer.set_mail_from(mail_from, mail_body)
                mailer.set_mail_to(recipients, mail_body)
                mailer.set_subject(f"[ADMIN ALERT] New Order #{order.oid} Placed", mail_body)
                
                email_content = render_to_string("email/customer_order_confirmation.html", context)
                mailer.set_html_content(email_content, mail_body)

                # Send the email
                response = mailer.send(mail_body)
                print(f"Admin email send response: {response}")
            except Exception as mail_error:
                print(f"MailerSend error: {str(mail_error)}")
                # Try Django's built-in mail as a fallback
                send_mail(
                    subject=f"[ADMIN ALERT] New Order #{order.oid} Placed",
                    message=f"New order placed with ID: {order.oid}. Total amount: ${order.total}. Payment status: {order.payment_status}",
                    from_email=settings.FROM_EMAIL,
                    recipient_list=[admin_email],
                    fail_silently=False,
                    html_message=email_content
                )
                print("Sent admin notification using Django's built-in email function")
            
            print(f"Admin notification sent successfully for order {order.oid}")
            
        except Exception as e:
            print(f"Admin notification error: {str(e)}")
            print(f"Detailed error: {traceback.format_exc()}")

    def create(self, request):
        payload = request.data

        full_name = payload["full_name"]
        email = payload["email"]
        mobile = payload["mobile"]
        address = payload["address"]
        city = payload["city"]
        state = payload["state"]
        country = payload["country"]
        cart_id = payload["cart_id"]
        user_id = payload["user_id"]
        payment_method = payload.get("payment_method", "stripe")

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
            payment_method=payment_method,
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
        
        # Get all order items for this order
        order_items = CartOrderItem.objects.filter(order=order)
        
        # Send admin notification
        self._send_admin_notification(order, order_items)

        return Response(
            {"message": "Order Created Successfully", "order_oid": order.oid},
            status=status.HTTP_201_CREATED,
        )


import logging

logger = logging.getLogger(__name__)

class CheckoutView(generics.RetrieveAPIView):
    serializer_class = CartOrderSerializer
    lookup_field = "order_oid"
    permission_classes = [
        AllowAny,
    ]

    def get_object(self):
        order_oid = self.kwargs["order_oid"]
        logger.info(f"Fetching CartOrder with oid: {order_oid}")
        try:
            order = CartOrder.objects.get(oid=order_oid)
            return order
        except CartOrder.DoesNotExist:
            logger.error(f"CartOrder with oid {order_oid} does not exist.")
            # Properly handle the not found case by using Django's standard 404 handling
            from django.http import Http404
            raise Http404(f"Order with ID {order_oid} not found")


class CouponAPIView(generics.CreateAPIView):
    serializer_class = CouponSerializer
    queryset = Coupon.objects.all()
    permission_classes = [
        AllowAny,
    ]

    def create(self, request):
        payload = request.data

        order_oid = payload["order_oid"]
        coupon_code = payload["coupon_code"]

        order = CartOrder.objects.get(oid=order_oid)
        coupon = Coupon.objects.filter(code=coupon_code).first()

        if coupon:
            order_items = CartOrderItem.objects.filter(
                order=order, vendor=coupon.vendor
            )

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

                        return Response(
                            {
                                "message": "Coupon Successfully Activated",
                                "status": "success",
                            },
                            status=status.HTTP_200_OK,
                        )
                    else:
                        return Response(
                            {
                                "message": "Coupon Already Activated",
                                "status": "warning",
                            },
                            status=status.HTTP_200_OK,
                        )
            else:
                return Response(
                    {
                        "message": "This coupon is not valid for the items in your cart",
                        "status": "error",
                    },
                    status=status.HTTP_200_OK,
                )
        else:
            return Response(
                {"message": "Coupon Does not Exists", "status": "error"},
                status=status.HTTP_200_OK,
            )


class StripeCheckoutAPIView(generics.CreateAPIView):
    serializer_class = CartOrderSerializer
    permission_classes = [
        AllowAny,
    ]
    queryset = CartOrder.objects.all()

    def create(self, *args, **kwargs):
        order_oid = self.kwargs["order_oid"]
        try:
            order = CartOrder.objects.get(oid=order_oid)
        except CartOrder.DoesNotExist:
            logger.error(f"Order with oid {order_oid} not found during Stripe checkout")
            return Response(
                {"message": "Order not Found"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            checkout_session = stripe.checkout.Session.create(
                customer_email=order.email,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": order.full_name,
                            },
                            "unit_amount": int(order.total * 100),
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url="http://localhost:5173/payment-success/"
                + order_oid
                + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url="http://localhost:5173/payment-failed/?session_id={CHECKOUT_SESSION_ID}",
            )

            order.stripe_session_id = checkout_session.id
            order.save()

            return redirect(checkout_session.url)
        except stripe.error.StripeError as e:
            return Response(
                {
                    "error": f"Something went wrong while creating checkout session: {str(e)}"
                }
            )


def calculate_vendor_totals(order_items, vendor):
    vendor_items = [item for item in order_items if item.vendor.id == vendor.id]
    sub_total = sum(item.sub_total for item in vendor_items)
    shipping_total = sum(item.shipping_amount for item in vendor_items)
    return {
        "vendor_sub_total": sub_total,
        "vendor_shipping_total": shipping_total,
        "vendor_items": vendor_items,
    }


def get_access_token(client_id, secret_id):
    try:
        print("Getting PayPal access token...")
        token_url = "https://api.sandbox.paypal.com/v1/oauth2/token"
        data = {"grant_type": "client_credentials"}
        auth = (client_id, secret_id)  # Perbaiki format auth
        print("Making token request to:", token_url)

        response = requests.post(token_url, data=data, auth=auth)
        print("Token response status:", response.status_code)
        print("Token response:", response.text)

        if response.status_code == 200:
            token = response.json()["access_token"]
            print("Got access token:", token[:10] + "...")
            return token
        else:
            raise Exception(
                f"Failed to get access token: {response.status_code} - {response.text}"
            )

    except Exception as e:
        print("Error getting access token:", str(e))
        print(traceback.format_exc())
        raise


class PaymentSuccessView(generics.CreateAPIView):
    serializer_class = CartOrderSerializer
    permission_classes = [
        AllowAny,
    ]
    queryset = CartOrder.objects.all()

    def _get_paypal_order_status(self, paypal_order_id):
        """Verify PayPal order status"""
        try:
            print("Verifying PayPal payment...")
            paypal_api_url = (
                f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{paypal_order_id}"
            )
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {get_access_token(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET_ID)}",
            }

            response = requests.get(paypal_api_url, headers=headers)
            print("PayPal API Response:", response.status_code, response.text)

            if response.status_code == 200:
                return response.json().get("status")
            return None

        except Exception as e:
            print(f"PayPal verification error: {str(e)}")
            return None

    def _send_vendor_notification(self, vendor, order, order_items):
        """Send email notification to vendor"""
        try:
            context = {
                "order": order,
                "order_items": order_items,
                "vendor": vendor,
                **calculate_vendor_totals(order_items, vendor),
            }

            mail_body = {}
            mail_from = {
                "name": "Koshimart",
                "email": settings.FROM_EMAIL,
            }
            recipients = [
                {
                    "name": vendor.name,
                    "email": vendor.user.email,
                }
            ]
            
            # Create notification
            notification = Notification.objects.create(
                vendor=vendor,
                order=order,
                seen=False,
                type="vendor"
            )
            notification.save()
            
            # Send an email
            mailer = emails.NewEmail(settings.MAILERSEND_API_KEY)
            mailer.set_mail_from(mail_from, mail_body)
            mailer.set_mail_to(recipients, mail_body)
            mailer.set_subject(f"New Order on Koshimart - #{order.oid}", mail_body)
            mailer.set_html_content(
                render_to_string("email/vendor_sale.html", context), mail_body
            )
            
            mailer.send(mail_body)
            print(f"Notification sent to vendor {vendor.name} for order {order.oid}")
            
        except Exception as e:
            print(f"Error sending vendor notification: {str(e)}")
            print(traceback.format_exc())

    def _send_customer_notification(self, order, order_items):
        """Send email notification to customer"""
        try:
            context = {
                "order": order,
                "order_items": order_items,
            }

            mail_body = {}
            mail_from = {
                "name": "Koshimart",
                "email": settings.FROM_EMAIL,
            }
            recipients = [
                {
                    "name": order.full_name,
                    "email": order.email,
                }
            ]

            mailer = emails.NewEmail(settings.MAILERSEND_API_KEY)
            mailer.set_mail_from(mail_from, mail_body)
            mailer.set_mail_to(recipients, mail_body)
            mailer.set_subject("Order placed successfully", mail_body)
            mailer.set_html_content(
                render_to_string("email/customer_order_confirmation.html", context),
                mail_body,
            )

            mailer.send(mail_body)
        except Exception as e:
            print(f"Customer notification error: {traceback.format_exc()}")

    def _send_admin_notification(self, order, order_items):
        """Send email notification to admin"""
        try:
            print(f"Attempting to send admin notification for order {order.oid}")
            
            # First, create a database notification for admin users
            try:
                # Find admin users
                admin_users = User.objects.filter(is_superuser=True)
                print(f"Found {admin_users.count()} admin users")
                
                # Create notification for each admin
                for admin in admin_users:
                    notification = Notification.objects.create(
                        user=admin,
                        order=order,
                        seen=False,
                        type="admin"
                    )
                    notification.save()
                    print(f"Created database notification for admin: {admin.email}")
            except Exception as notif_error:
                print(f"Error creating admin database notification: {str(notif_error)}")
            
            # Then continue with email notification
            context = {
                "order": order,
                "order_items": order_items,
                "is_admin_notification": True,
            }

            mail_body = {}
            mail_from = {
                "name": "Koshimart System",
                "email": settings.FROM_EMAIL,
            }
            
            # Admin email - hardcoded to ensure it's correct
            admin_email = "deepxpacelab@gmail.com"
            
            recipients = [
                {
                    "name": "Admin",
                    "email": admin_email,
                }
            ]
            
            print(f"Sending admin notification to {admin_email}")
            print(f"Using FROM_EMAIL: {settings.FROM_EMAIL}")
            print(f"Using MAILERSEND_API_KEY: {settings.MAILERSEND_API_KEY[:5]}...")

            # First try with MailerSend
            try:
                mailer = emails.NewEmail(settings.MAILERSEND_API_KEY)
                mailer.set_mail_from(mail_from, mail_body)
                mailer.set_mail_to(recipients, mail_body)
                mailer.set_subject(f"[ADMIN ALERT] New Order #{order.oid} Placed", mail_body)
                
                email_content = render_to_string("email/customer_order_confirmation.html", context)
                mailer.set_html_content(email_content, mail_body)

                # Send the email
                response = mailer.send(mail_body)
                print(f"Admin email send response: {response}")
            except Exception as mail_error:
                print(f"MailerSend error: {str(mail_error)}")
                # Try Django's built-in mail as a fallback
                send_mail(
                    subject=f"[ADMIN ALERT] New Order #{order.oid} Placed",
                    message=f"New order placed with ID: {order.oid}. Total amount: ${order.total}. Payment status: {order.payment_status}",
                    from_email=settings.FROM_EMAIL,
                    recipient_list=[admin_email],
                    fail_silently=False,
                    html_message=email_content
                )
                print("Sent admin notification using Django's built-in email function")
            
            print(f"Admin notification sent successfully for order {order.oid}")
            
        except Exception as e:
            print(f"Admin notification error: {str(e)}")
            print(f"Detailed error: {traceback.format_exc()}")

    def _process_successful_payment(self, order, order_items, transaction_id=None):
        """Process successful payment and send notifications"""
        if order.payment_status != "pending":
            return Response(
                {"message": "Payment has already been processed", "status": "info"}
            )

        # Only mark non-COD orders as paid
        if order.payment_method != "Cash On Delivery":
            order.payment_status = "paid"
        # Cash on Delivery orders should remain pending until delivery
        else:
            order.payment_status = "pending"
            
        if transaction_id:  # Save the transaction ID
            order.paypal_order_id = transaction_id
        # Mark Cash on Delivery orders as processing
        if order.payment_method == "Cash On Delivery":
            order.order_status = "processing"
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
        
        # Send admin notification
        self._send_admin_notification(order, order_items)

        return Response(
            {"message": "Payment completed successfully", "status": "success"}
        )

    def create(self, request, *args, **kwargs):
        try:
            payload = request.data
            order_oid = payload.get("order_oid")
            session_id = payload.get("session_id")
            paypal_order_id = payload.get("paypal_order_id")

            if not order_oid:
                return Response(
                    {"message": "Order ID is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                order = CartOrder.objects.get(oid=order_oid)
                order_items = CartOrderItem.objects.filter(order=order)
            except CartOrder.DoesNotExist:
                return Response(
                    {"message": "Order not found"}, status=status.HTTP_404_NOT_FOUND
                )
                
            # Cash on Delivery payment
            if order.payment_method == "Cash On Delivery":
                return self._process_successful_payment(order, order_items)

            # PayPal Payment
            if paypal_order_id and paypal_order_id != "null":
                paypal_status = self._get_paypal_order_status(paypal_order_id)

                if paypal_status == "COMPLETED":
                    return self._process_successful_payment(
                        order, order_items, transaction_id=paypal_order_id
                    )
                elif paypal_status:
                    return Response(
                        {
                            "message": "Payment pending. Please complete your payment",
                            "status": "warning",
                        }
                    )

            # Stripe Payment
            if session_id and session_id != "null":
                try:
                    session = stripe.checkout.Session.retrieve(session_id)

                    if session.payment_status == "paid":
                        return self._process_successful_payment(order, order_items)
                    elif session.payment_status == "unpaid":
                        return Response(
                            {
                                "message": "Payment pending. Please complete your payment",
                                "status": "warning",
                            }
                        )
                    elif session.payment_status == "cancelled":
                        return Response(
                            {
                                "message": "Payment cancelled. Please try again or contact support",
                                "status": "error",
                            }
                        )
                except stripe.error.StripeError as e:
                    return Response(
                        {
                            "message": "Payment verification failed. Please try again or contact support",
                            "error": str(e),
                            "status": "error",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            return Response(
                {"message": "Invalid payment information provided", "status": "error"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            print(f"Unexpected error: {traceback.format_exc()}")
            return Response(
                {
                    "message": "An unexpected error occurred",
                    "error": str(e),
                    "status": "error",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ReviewListAPIView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [
        AllowAny,
    ]

    def get_queryset(self):
        product_id = self.kwargs.get("product_id")
        
        # Handle undefined or invalid product_id
        if product_id == 'undefined' or not product_id:
            logger.warning(f"Invalid product_id: {product_id}")
            return Review.objects.none()
        
        try:
            product = Product.objects.get(id=product_id)
            reviews = Review.objects.filter(product=product)
            return reviews
        except (Product.DoesNotExist, ValueError):
            logger.warning(f"Product with id {product_id} does not exist")
            return Review.objects.none()

    def create(self, request, *args, **kwargs):
        payload = request.data

        user_id = payload.get("user_id")
        product_id = payload.get("product_id")
        rating = payload.get("rating")
        review = payload.get("review")
        
        # Validate required fields
        if not all([user_id, product_id, rating, review]):
            return Response(
                {"message": "Missing required fields", "status": "error"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)
            product = Product.objects.get(id=product_id)
            
            Review.objects.create(
                user=user,
                product=product,
                rating=rating,
                review=review,
            )
            
            return Response(
                {"message": "Review created successfully", "status": "success"},
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                {"message": "User not found", "status": "error"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Product.DoesNotExist:
            return Response(
                {"message": "Product not found", "status": "error"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error creating review: {str(e)}")
            return Response(
                {"message": f"Error creating review: {str(e)}", "status": "error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SearchProductAPIView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        query = self.request.GET.get("query", "")
        category = self.request.GET.get("category")
        min_price = self.request.GET.get("min_price")
        max_price = self.request.GET.get("max_price")
        sort = self.request.GET.get("sort")
        in_stock = self.request.GET.get("in_stock")

        queryset = Product.objects.filter(status="published")

        if query:
            queryset = queryset.filter(title__icontains=query)

        if category:
            queryset = queryset.filter(category_id=category)

        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        if max_price:
            queryset = queryset.filter(price__lte=min_price)

        if in_stock == "true":
            queryset = queryset.filter(in_stock=True)

        if sort:
            if sort == "price_asc":
                queryset = queryset.order_by("price")
            elif sort == "price_desc":
                queryset = queryset.order_by("-price")
            elif sort == "rating":
                queryset = queryset.order_by("-rating")
            elif sort == "newest":
                queryset = queryset.order_by("-date")

        return queryset


from rest_framework.views import APIView
import logging

logger = logging.getLogger(__name__)

class CartDeleteAPIView(APIView):
    def delete(self, request, cart_id, item_id, user_id=None):
        logger.info(f"Received DELETE request for cart_id: {cart_id}, item_id: {item_id}, user_id: {user_id}")
        try:
            if user_id:
                user = User.objects.get(id=user_id)
                cart_item = Cart.objects.get(id=item_id, cart_id=cart_id, user=user)
            else:
                cart_item = Cart.objects.get(id=item_id, cart_id=cart_id)

            cart_item.delete()
            logger.info(f"Successfully deleted item_id: {item_id} from cart_id: {cart_id}")
            return Response({"message": "Item removed successfully"}, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            logger.error(f"Item not found in cart for cart_id: {cart_id}, item_id: {item_id}")
            return Response({"error": "Item not found in cart"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error while deleting item from cart: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from uuid import uuid4

class CreateOrderAPIView(APIView):
    def post(self, request):
        logger.info("Received POST request for order creation")
        logger.info(f"Request data: {request.data}")
        try:
            data = request.data
            user_id = data.get("user_id")
            cart_id = data.get("cart_id", "")
            user = None
            
            if user_id and user_id != "undefined" and user_id != "0":
                try:
                    user = User.objects.get(id=user_id)
                    logger.info(f"Found user with id {user_id}")
                except User.DoesNotExist:
                    logger.warning(f"User with id {user_id} does not exist. Proceeding without a user.")
                    user = None
            else:
                logger.warning("No valid user ID provided. Proceeding without a user.")
                
                # Try to get user from authenticated request if available
                if request.user and request.user.is_authenticated:
                    user = request.user
                    logger.info(f"Using authenticated user: {user.email} (id: {user.id})")
                else:
                    user = None

            # Generate a date-based order ID with a shorter random component
            import datetime
            import random
            import string
            
            today = datetime.datetime.now()
            date_prefix = today.strftime("%Y%m%d")
            # Generate 6 random alphanumeric characters
            random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            unique_oid = f"{date_prefix}-{random_suffix}"
            
            # Create the order
            order = CartOrder.objects.create(
                oid=unique_oid,
                buyer=user,
                full_name=data.get("full_name"),
                email=data.get("email"),
                mobile=data.get("mobile"),
                address=data.get("address"),
                city=data.get("city"),
                state=data.get("state"),
                country=data.get("country"),
                payment_method=data.get("payment_method", "stripe"),
            )

            # Get cart items and add them to the order
            if cart_id:
                cart_items = Cart.objects.filter(cart_id=cart_id)
                logger.info(f"Found {cart_items.count()} cart items for cart_id {cart_id}")
                
                total_shipping = Decimal(0.00)
                total_tax = Decimal(0.00)
                total_service_fee = Decimal(0.00)
                total_sub_total = Decimal(0.00)
                total_initial_total = Decimal(0.00)
                total_total = Decimal(0.00)
                
                # Add each cart item to the order
                for c in cart_items:
                    if c.product and c.product.vendor:
                        # Generate unique OID for each order item
                        item_random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                        item_oid = f"{date_prefix}-{item_random_suffix}"
                        
                        CartOrderItem.objects.create(
                            oid=item_oid,
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

                        # Add the vendor to the order
                        order.vendor.add(c.product.vendor)
                
                # Update order totals
                order.sub_total = total_sub_total
                order.shipping_amount = total_shipping
                order.tax_fee = total_tax
                order.service_fee = total_service_fee
                order.initial_total = total_initial_total
                order.total = total_total
                order.save()
                
                logger.info(f"Updated order totals: total={total_total}, items={cart_items.count()}")
            else:
                logger.warning("No cart_id provided, order created without items")

            logger.info(f"Order created successfully with OID: {order.oid}")
            return Response({"order_oid": order.oid, "message": "Order created successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error while creating order: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CashOnDeliveryAPIView(generics.CreateAPIView):
    serializer_class = CartOrderSerializer
    permission_classes = [
        AllowAny,
    ]
    queryset = CartOrder.objects.all()

    def create(self, request, *args, **kwargs):
        order_oid = self.kwargs["order_oid"]
        
        try:
            order = CartOrder.objects.get(oid=order_oid)
            
            if not order:
                return Response(
                    {"error": "Order not found", "success": False}, 
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # Update order payment method and status
            order.payment_method = "Cash On Delivery"
            order.payment_status = "pending"
            order.order_status = "processing"
            order.save()
            
            # Get all order items for this order
            order_items = CartOrderItem.objects.filter(order=order)
            
            # Notify vendors about new order
            vendors = set()
            
            for item in order_items:
                product = item.product
                if product.vendor not in vendors:
                    vendors.add(product.vendor)
                    self._send_vendor_notification(product.vendor, order, order_items.filter(product__vendor=product.vendor))
            
            # Send admin notification
            self._send_admin_notification(order, order_items)
            
            # Clear the cart after successful checkout
            cart_id = request.data.get("cart_id", None)
            if cart_id:
                Cart.objects.filter(cart_id=cart_id).delete()
                logger.info(f"Cart {cart_id} cleared after successful checkout")
                    
            return Response(
                {
                    "success": True,
                    "message": "Order placed successfully with Cash on Delivery!",
                    "order_oid": order_oid,
                },
                status=status.HTTP_200_OK
            )
            
        except CartOrder.DoesNotExist:
            return Response(
                {"error": "Order not found", "success": False}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error processing Cash on Delivery order: {str(e)}")
            return Response(
                {"error": str(e), "success": False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    def _send_vendor_notification(self, vendor, order, order_items):
        """Send email notification to vendor"""
        try:
            context = {
                "order": order,
                "order_items": order_items,
                "vendor": vendor,
                **calculate_vendor_totals(order_items, vendor),
            }

            mail_body = {}
            mail_from = {
                "name": "Koshimart",
                "email": settings.FROM_EMAIL,
            }
            recipients = [
                {
                    "name": vendor.name,
                    "email": vendor.user.email,
                }
            ]
            
            # Create notification
            notification = Notification.objects.create(
                vendor=vendor,
                order=order,
                seen=False,
                type="vendor"
            )
            notification.save()
            
            # Send an email
            mailer = emails.NewEmail(settings.MAILERSEND_API_KEY)
            mailer.set_mail_from(mail_from, mail_body)
            mailer.set_mail_to(recipients, mail_body)
            mailer.set_subject(f"New Order on Koshimart - #{order.oid}", mail_body)
            mailer.set_html_content(
                render_to_string("email/vendor_sale.html", context), mail_body
            )
            
            mailer.send(mail_body)
            print(f"Notification sent to vendor {vendor.name} for order {order.oid}")
            
        except Exception as e:
            print(f"Error sending vendor notification: {str(e)}")
            print(traceback.format_exc())
            
    def _send_admin_notification(self, order, order_items):
        """Send email notification to admin"""
        try:
            print(f"Attempting to send admin notification for order {order.oid}")
            
            # First, create a database notification for admin users
            try:
                # Find admin users
                admin_users = User.objects.filter(is_superuser=True)
                print(f"Found {admin_users.count()} admin users")
                
                # Create notification for each admin
                for admin in admin_users:
                    notification = Notification.objects.create(
                        user=admin,
                        order=order,
                        seen=False,
                        type="admin"
                    )
                    notification.save()
                    print(f"Created database notification for admin: {admin.email}")
            except Exception as notif_error:
                print(f"Error creating admin database notification: {str(notif_error)}")
            
            # Then continue with email notification
            context = {
                "order": order,
                "order_items": order_items,
                "is_admin_notification": True,
            }

            mail_body = {}
            mail_from = {
                "name": "Koshimart System",
                "email": settings.FROM_EMAIL,
            }
            
            # Admin email - hardcoded to ensure it's correct
            admin_email = "deepxpacelab@gmail.com"
            
            recipients = [
                {
                    "name": "Admin",
                    "email": admin_email,
                }
            ]
            
            print(f"Sending admin notification to {admin_email}")
            print(f"Using FROM_EMAIL: {settings.FROM_EMAIL}")
            print(f"Using MAILERSEND_API_KEY: {settings.MAILERSEND_API_KEY[:5]}...")

            # First try with MailerSend
            try:
                mailer = emails.NewEmail(settings.MAILERSEND_API_KEY)
                mailer.set_mail_from(mail_from, mail_body)
                mailer.set_mail_to(recipients, mail_body)
                mailer.set_subject(f"[ADMIN ALERT] New Order #{order.oid} Placed", mail_body)
                
                email_content = render_to_string("email/customer_order_confirmation.html", context)
                mailer.set_html_content(email_content, mail_body)

                # Send the email
                response = mailer.send(mail_body)
                print(f"Admin email send response: {response}")
            except Exception as mail_error:
                print(f"MailerSend error: {str(mail_error)}")
                # Try Django's built-in mail as a fallback
                send_mail(
                    subject=f"[ADMIN ALERT] New Order #{order.oid} Placed",
                    message=f"New order placed with ID: {order.oid}. Total amount: ${order.total}. Payment status: {order.payment_status}",
                    from_email=settings.FROM_EMAIL,
                    recipient_list=[admin_email],
                    fail_silently=False,
                    html_message=email_content
                )
                print("Sent admin notification using Django's built-in email function")
            
            print(f"Admin notification sent successfully for order {order.oid}")
            
        except Exception as e:
            print(f"Admin notification error: {str(e)}")
            print(f"Detailed error: {traceback.format_exc()}")


class SiteSettingsAPIView(APIView):
    """
    API view to get site settings.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get site settings."""
        settings = SiteSettings.get_settings()
        data = {
            'service_fee_percentage': float(settings.service_fee_percentage),
            'currency_symbol': settings.currency_symbol,
            'currency_code': settings.currency_code,
        }
        return Response(data)
