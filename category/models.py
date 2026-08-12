from django.db import models
from django.urls import reverse


class Category(models.Model):

    category_name = models.CharField(
        max_length=50,
        unique=True
    )

    slug = models.SlugField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        max_length=255,
        blank=True
    )

    cat_image = models.ImageField(
        upload_to='photos/categories',
        blank=True
    )

    # =====================================================
    # SEO FIELDS
    # =====================================================

    seo_title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="SEO title displayed in Google search results."
    )

    h1_title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Main H1 heading displayed on the category page."
    )

    meta_description = models.TextField(
        blank=True,
        null=True,
        help_text="SEO meta description displayed in search results."
    )

    primary_keyword = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Primary SEO keyword for this category."
    )

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def get_url(self):
        return reverse(
            'products_by_category',
            args=[self.slug]
        )

    def __str__(self):
        return self.category_name