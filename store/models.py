from django.db import models
from category.models import Category
from django.urls import reverse
from django.utils.text import slugify
from accounts.models import Account


class Product(models.Model):
    product_name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    price = models.IntegerField()
    quantity = models.CharField(max_length=50, blank=True, null=True)
    images = models.ImageField(upload_to='photo/products')
    stock = models.IntegerField()
    is_available = models.BooleanField(default=True)
    is_new_arrival = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    is_combo = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    
    # Existing fields
    key_ingredient = models.TextField(blank=True, null=True)
    all_ingredients = models.TextField(blank=True, null=True)

    # ✅ Rename old how_to_use → packaging_details
    packaging_details = models.TextField(blank=True, null=True)

    # ✅ Add new how_to_use field
    how_to_use = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.product_name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_url(self):
        return reverse('product_detail', args=[self.category.slug, self.slug])

    def get_highlights_list(self):
        return self.highlights.strip().split('\n') if self.highlights else []

    def __str__(self):
        return self.product_name



variation_category_choice = (
    ('color', 'color'),
    ('size', 'size'),
)


class VariationManager(models.Manager):
    def colors(self):
        return super().filter(variation_category='color', is_active=True)

    def sizes(self):
        return super().filter(variation_category='size', is_active=True)


class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation_category = models.CharField(max_length=100, choices=variation_category_choice)
    variation_value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now=True)

    objects = VariationManager()

    def __str__(self):
        return self.variation_value


class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100, blank=True)
    review = models.TextField(max_length=500, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject


class ProductGallery(models.Model):
    product = models.ForeignKey(Product, default=None, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='store/products', max_length=255)

    def __str__(self):
        return self.product.product_name

    class Meta:
        verbose_name = 'product gallery'
        verbose_name_plural = 'product gallery'


class Wishlist(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.email} - {self.product.product_name}"

class SmallBanner(models.Model):
    video = models.FileField(upload_to='small_banners/')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Small Banner {self.id}"
    
class Benefit(models.Model):
    product = models.ForeignKey(Product, related_name='benefits', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='benefit_images/', blank=True, null=True)

    def __str__(self):
        return self.title
