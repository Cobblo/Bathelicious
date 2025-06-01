from django.contrib import admin
from .models import Product, Variation, ReviewRating, ProductGallery
import admin_thumbnails
from .models import SmallBanner

@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'price', 'stock', 'category', 'modified_date', 'is_available', 'is_combo', 'is_bestseller')
    prepopulated_fields = {'slug': ('product_name',)}
    inlines = [ProductGalleryInline]  # Include benefits
    search_fields = ('product_name', 'description', 'category__category_name')
    ordering = ('-modified_date',)
    list_per_page = 25
    readonly_fields = ('modified_date',)

class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category', 'variation_value', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('product', 'variation_category', 'variation_value')
    search_fields = ('product__product_name', 'variation_value')
    list_per_page = 25



admin.site.register(Product, ProductAdmin)
admin.site.register(Variation, VariationAdmin)
admin.site.register(ReviewRating)
admin.site.register(ProductGallery)
admin.site.register(SmallBanner)
