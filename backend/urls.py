"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from store.views import CartDeleteAPIView
from api.views import proxy_s3_media

schema_view = get_schema_view(
    openapi.Info(
        title='Django Ecommerce Backend APIs',
        default_version='v1',
        description='Official backend APIs documentation for Django Ecommerce web applications',
        contact=openapi.Contact(email='riorajaa2018@gmail.com'),
        license=openapi.License(name='BSD License')    
    ),
    public=True,
    permission_classes=(permissions.AllowAny,)
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.urls')),
    
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += [
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('api/v1/cart-delete/<str:cart_id>/<int:item_id>/', CartDeleteAPIView.as_view(), name='cart-delete'),
    path('api/v1/cart-delete/<str:cart_id>/<int:item_id>/<int:user_id>/', CartDeleteAPIView.as_view(), name='cart-delete-with-user'),
    path('media-proxy/<path:path>', proxy_s3_media, name='media_proxy'),
]
