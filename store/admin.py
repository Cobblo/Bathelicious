from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
import admin_thumbnails

from .models import (
    Product, Variation, ReviewRating, ProductGallery,
    Wishlist, SmallBanner, KeyIngredient, AboutSettings, ReviewVideo,
    Coupon, CouponUsage, ProductFAQ
)


# --- helpers ---------------------------------------------------------------
def safe_unregister(model):
    try:
        admin.site.unregister(model)
    except NotRegistered:
        pass


def safe_register(model, admin_class=None):
    safe_unregister(model)
    if admin_class:
        admin.site.register(model, admin_class)
    else:
        admin.site.register(model)


# --- inlines ---------------------------------------------------------------
@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1


class KeyIngredientInline(admin.TabularInline):
    model = KeyIngredient
    extra = 1


class ProductFAQInline(admin.TabularInline):
    model = ProductFAQ
    extra = 10
    max_num = 10


# --- ModelAdmins -----------------------------------------------------------
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'product_name', 'price', 'stock', 'category',
        'is_available', 'is_featured', 'is_new_arrival'
    )
    prepopulated_fields = {'slug': ('product_name',)}
    inlines = [ProductGalleryInline, KeyIngredientInline, ProductFAQInline]
    list_filter = (
        'category', 'is_available', 'is_featured',
        'is_new_arrival', 'is_combo', 'is_bestseller'
    )
    search_fields = ('product_name', 'slug')


class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category', 'variation_value', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('product', 'variation_category', 'variation_value')


class ReviewRatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('product__product_name', 'user__email')


class AboutSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "updated_at")


@admin.register(ReviewVideo)
class ReviewVideoAdmin(admin.ModelAdmin):
    list_display = ('video', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    ordering = ('order',)
    list_per_page = 10


class CouponAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'discount_percentage',
        'is_active',
        'valid_from',
        'valid_to',
        'minimum_amount',
        'one_time_per_user',
        'first_order_only',
    )
    search_fields = ('code',)
    list_filter = ('is_active', 'one_time_per_user', 'first_order_only')
    filter_horizontal = ('categories', 'products')


class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ('user', 'coupon', 'order_id', 'used_at')
    search_fields = ('user__email', 'coupon__code', 'order_id')


# --- Safe registrations ----------------------------------------------------
safe_register(Product, ProductAdmin)
safe_register(ProductFAQ)
safe_register(Variation, VariationAdmin)
safe_register(ReviewRating, ReviewRatingAdmin)
safe_register(ProductGallery)
safe_register(Wishlist)
safe_register(SmallBanner)
safe_register(KeyIngredient)
safe_register(AboutSettings, AboutSettingsAdmin)
safe_register(Coupon, CouponAdmin)
safe_register(CouponUsage, CouponUsageAdmin)