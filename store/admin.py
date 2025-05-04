from django.contrib import admin
from django.contrib import messages
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

# Register your models here.


class GalleryInline(admin.TabularInline):
    model = Gallery
    extra = 0
    
    def get_max_num(self, request, obj=None, **kwargs):
        return 10  # Limit to 10 images to prevent upload issues


class SpecificationInline(admin.TabularInline):
    model = Specification
    extra = 0


class SizeInline(admin.TabularInline):
    model = Size
    extra = 0


class ColorInline(admin.TabularInline):
    model = Color
    extra = 0


class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "price",
        "category",
        "shipping_amount",
        "stock_qty",
        "in_stock",
        "vendor",
        "featured",
    ]
    list_editable = ["featured"]
    list_filter = ["date"]
    search_fields = ["title"]
    inlines = [GalleryInline, SpecificationInline, SizeInline, ColorInline]
    save_on_top = True
    
    def save_model(self, request, obj, form, change):
        """Override save_model to add validation and handle image uploads."""
        try:
            # Check if title is not too long to avoid DB errors
            if len(obj.title) > 90:
                obj.title = obj.title[:90]
                messages.warning(request, "Title was truncated to 90 characters")
            
            # Ensure slug doesn't exceed the max length
            if obj.slug and len(obj.slug) > 40:
                obj.slug = obj.slug[:40]
                messages.warning(request, "Slug was truncated to 40 characters")
                
            # Now save the model
            super().save_model(request, obj, form, change)
            messages.success(request, f"Product '{obj.title}' saved successfully")
        except Exception as e:
            messages.error(request, f"Error saving product: {str(e)}")


class CartOrderAdmin(admin.ModelAdmin):
    list_display = ["oid", "buyer", "date"]
    list_filter = ["date"]
    search_fields = ["oid"]


class SiteSettingsAdmin(admin.ModelAdmin):
    """
    Admin interface for SiteSettings model.
    Prevents adding new instances as this is a singleton model.
    """
    def has_add_permission(self, request):
        # Only allow adding if no instances exist
        return SiteSettings.objects.count() == 0
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the settings object
        return False


admin.site.register(Category)
admin.site.register(Product, ProductAdmin)

admin.site.register(Cart)
admin.site.register(CartOrder, CartOrderAdmin)
admin.site.register(CartOrderItem)

admin.site.register(ProductFaq)
admin.site.register(Review)
admin.site.register(Wishlist)
admin.site.register(Notification)
admin.site.register(Coupon)
admin.site.register(Tax)
admin.site.register(SiteSettings, SiteSettingsAdmin)
