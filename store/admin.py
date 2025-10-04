# store/admin.py
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
import admin_thumbnails

from .models import (
    Product, Variation, ReviewRating, ProductGallery,
    Wishlist, SmallBanner, KeyIngredient, AboutSettings
)

# --- helpers ---------------------------------------------------------------
def safe_unregister(model):
    try:
        admin.site.unregister(model)
    except NotRegistered:
        pass

def safe_register(model, admin_class=None):
    """Unregister if already registered, then (re)register."""
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

# --- ModelAdmins -----------------------------------------------------------
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'price', 'stock', 'category',
                    'is_available', 'is_featured', 'is_new_arrival')
    prepopulated_fields = {'slug': ('product_name',)}
    inlines = [ProductGalleryInline, KeyIngredientInline]
    list_filter = ('category', 'is_available', 'is_featured',
                   'is_new_arrival', 'is_combo', 'is_bestseller')
    search_fields = ('product_name', 'slug')

class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category', 'variation_value', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('product', 'variation_category', 'variation_value')

class ReviewRatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('product_product_name', 'user_email')

class AboutSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "updated_at")

# --- Safe registrations (no duplicates) -----------------------------------
safe_register(Product, ProductAdmin)
safe_register(Variation, VariationAdmin)
safe_register(ReviewRating, ReviewRatingAdmin)
safe_register(ProductGallery)     # can be registered and also used as inline
safe_register(Wishlist)
safe_register(SmallBanner)
safe_register(KeyIngredient)
safe_register(AboutSettings, AboutSettingsAdmin)