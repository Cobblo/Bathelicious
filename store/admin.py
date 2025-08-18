from django.contrib import admin
from .models import Product, Variation, ReviewRating, ProductGallery, Wishlist, SmallBanner, KeyIngredient
import admin_thumbnails


@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1


class KeyIngredientInline(admin.TabularInline):
    model = KeyIngredient
    extra = 1


class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'price', 'stock', 'category', 'is_available', 'is_featured', 'is_new_arrival')
    prepopulated_fields = {'slug': ('product_name',)}
    inlines = [ProductGalleryInline, KeyIngredientInline]


class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category', 'variation_value', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('product', 'variation_category', 'variation_value')


class ReviewRatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'status', 'created_at')
    list_filter = ('status', 'created_at')


admin.site.register(Product, ProductAdmin)
admin.site.register(Variation, VariationAdmin)
admin.site.register(ReviewRating, ReviewRatingAdmin)
admin.site.register(ProductGallery)
admin.site.register(Wishlist)
admin.site.register(SmallBanner)
admin.site.register(KeyIngredient)
