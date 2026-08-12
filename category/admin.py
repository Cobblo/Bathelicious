from django.contrib import admin
from .models import Category


class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        'category_name',
        'slug',
        'primary_keyword',
    )

    prepopulated_fields = {
        'slug': ('category_name',)
    }

    search_fields = (
        'category_name',
        'slug',
        'seo_title',
        'primary_keyword',
    )

    fieldsets = (
        (
            'Category Details',
            {
                'fields': (
                    'category_name',
                    'slug',
                    'description',
                    'cat_image',
                )
            }
        ),
        (
            'SEO Settings',
            {
                'fields': (
                    'seo_title',
                    'h1_title',
                    'meta_description',
                    'primary_keyword',
                )
            }
        ),
    )


admin.site.register(
    Category,
    CategoryAdmin
)