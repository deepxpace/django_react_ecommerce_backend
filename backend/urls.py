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
from api.views import proxy_s3_media, debug_image_paths, api_root, debug_cloudinary, test_image, media_proxy

schema_view = get_schema_view(
    openapi.Info(
        title="Kosimart API",
        default_version='v1',
        description="API Documentation for Kosimart E-commerce",
        terms_of_service="https://www.kosimart.com/terms/",
        contact=openapi.Contact(email="contact@kosimart.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Root URL - API information
    path('', api_root, name='api_root'),
    
    path('admin/', admin.site.urls),
    
    path('api/', include('api.urls')),
    
    # Direct media proxy endpoints
    path('media-proxy/<path:path>', proxy_s3_media, name='media_proxy'),
    path('debug-images/', debug_image_paths, name='debug_image_paths'),
    path('debug-cloudinary/', debug_cloudinary, name='debug_cloudinary'),
    path('test-image/<str:format>/', test_image, name='test_image'),
    
    # Redirect from media paths directly to the proxy
    path('media/<path:path>', media_proxy, name='media_direct'),
    
    # API Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
]

# Debug-only settings
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += [
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('api/v1/cart-delete/<str:cart_id>/<int:item_id>/', CartDeleteAPIView.as_view(), name='cart-delete'),
    path('api/v1/cart-delete/<str:cart_id>/<int:item_id>/<int:user_id>/', CartDeleteAPIView.as_view(), name='cart-delete-with-user'),
]
