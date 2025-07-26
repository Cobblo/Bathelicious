from django.contrib import admin
from .models import Product, Variation, ReviewRating, ProductGallery, SmallBanner, Benefit
import admin_thumbnails

# ✅ Inline for Product Gallery
@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

# ✅ Inline for Benefits
class BenefitInline(admin.TabularInline):
    model = Benefit
    extra = 1    

# ✅ Product Admin
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'product_name', 'price', 'stock', 'category', 'quantity',
        'modified_date', 'is_available', 'is_combo', 'is_bestseller'
    )
    prepopulated_fields = {'slug': ('product_name',)}
    inlines = [ProductGalleryInline, BenefitInline]
    search_fields = ('product_name', 'description', 'category__category_name')
    ordering = ('-modified_date',)
    list_per_page = 25
    readonly_fields = ('modified_date',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('product_name', 'slug', 'description', 'price', 'quantity', 'images', 'stock', 'category')
        }),
        ('Availability & Tags', {
            'fields': ('is_available', 'is_combo', 'is_bestseller')
        }),
        ('Ingredients & Details', {
            'fields': ('key_ingredient', 'all_ingredients', 'packaging_details', 'how_to_use')
        }),
        ('System Info', {
            'fields': ('modified_date',)
        }),
    )

# ✅ Variation Admin
class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category', 'variation_value', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('product', 'variation_category', 'variation_value')
    search_fields = ('product__product_name', 'variation_value')
    list_per_page = 25

# ✅ Register models
admin.site.register(Product, ProductAdmin)
admin.site.register(Variation, VariationAdmin)
admin.site.register(ReviewRating)
admin.site.register(ProductGallery)
admin.site.register(SmallBanner)
admin.site.register(Benefit)
