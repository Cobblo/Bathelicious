from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from category.models import Category
from accounts.models import Account
from django_ckeditor_5.fields import CKEditor5Field
from decimal import Decimal
from django.conf import settings
from django.utils import timezone

class Product(models.Model):
    product_name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = CKEditor5Field(config_name="default")
    price = models.IntegerField()
    quantity = models.CharField(max_length=50, blank=True, null=True)
    images = models.ImageField(upload_to='photo/products')
    stock = models.IntegerField()
    is_available = models.BooleanField(default=True)
    is_new_arrival = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_combo = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)

    # key_ingredients managed via KeyIngredient.related_name = 'key_ingredients'
    all_ingredients = models.TextField(blank=True, null=True)
    packaging_details = models.TextField(blank=True, null=True)
    how_to_use = models.TextField(blank=True, null=True)
    benefits = CKEditor5Field(config_name="default", blank=True, null=True)

    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

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

    def __str__(self):
        return self.product_name


class KeyIngredient(models.Model):
    product = models.ForeignKey(Product, related_name='key_ingredients', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='ingredients/')

    def __str__(self):
        return f"{self.name} ({self.product.product_name})"


variation_category_choice = (
    ('color', 'Color'),
    ('size', 'Size'),
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
        return self.subject or f"Review #{self.pk}"


class ProductGallery(models.Model):
    product = models.ForeignKey(Product, default=None, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='store/products', max_length=255)

    def __str__(self):
        return self.product.product_name

    class Meta:
        verbose_name = 'product gallery'
        verbose_name_plural = 'product galleries'


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


# NEW: About page images manageable via Admin
def upload_to_about(instance, filename):
    return f"about/{filename}"


class AboutSettings(models.Model):
    story_image = models.ImageField(upload_to=upload_to_about, blank=True, null=True)
    choose_image = models.ImageField(upload_to=upload_to_about, blank=True, null=True)
    impact_image = models.ImageField(upload_to=upload_to_about, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "About Page Settings"
        verbose_name_plural = "About Page Settings"

    def __str__(self):
        return "About Page Settings"


class ReviewVideo(models.Model):
    video = models.FileField(upload_to='review_videos/')
    order = models.PositiveIntegerField(default=0, help_text="Lower number = appears first")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']  # ✅ automatically sorts in ascending order

    def __str__(self):
        return str(self.video.name).split('/')[-1] if self.video else "Review Video"


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percentage = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    valid_from = models.DateTimeField(blank=True, null=True)
    valid_to = models.DateTimeField(blank=True, null=True)

    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    one_time_per_user = models.BooleanField(default=False)
    first_order_only = models.BooleanField(default=False)

    categories = models.ManyToManyField(Category, blank=True)
    products = models.ManyToManyField('Product', blank=True)

    def __str__(self):
        return self.code

    def validate_coupon(self, user, cart_items, Order):
        now = timezone.now()
        eligible_total = Decimal('0.00')

        for item in cart_items:
            item_total = Decimal(str(item.product.price)) * item.quantity

            if self.products.exists():
                if self.products.filter(id=item.product.id).exists():
                    eligible_total += item_total
                continue

            if self.categories.exists():
                if self.categories.filter(id=item.product.category.id).exists():
                    eligible_total += item_total
                continue

            eligible_total += item_total

        if not self.is_active:
            return False, "Coupon inactive", Decimal('0.00')

        if self.valid_from and now < self.valid_from:
            return False, "Coupon not started yet", Decimal('0.00')

        if self.valid_to and now > self.valid_to:
            return False, "Coupon expired", Decimal('0.00')

        if eligible_total <= 0:
            return False, "Not applicable for these products", Decimal('0.00')

        if eligible_total < self.minimum_amount:
            return False, f"Minimum ₹{self.minimum_amount} required", Decimal('0.00')

        if self.first_order_only and user.is_authenticated:
            if Order.objects.filter(user=user, is_ordered=True).exists():
                return False, "Only for first order", Decimal('0.00')

        if self.one_time_per_user and user.is_authenticated:
            if CouponUsage.objects.filter(user=user, coupon=self).exists():
                return False, "Already used", Decimal('0.00')

        discount = (Decimal(self.discount_percentage) / Decimal('100')) * eligible_total
        return True, "Coupon applied", discount.quantize(Decimal('0.01'))


class CouponUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=100, blank=True, null=True)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'coupon')

    def __str__(self):
        return f"{self.user} - {self.coupon.code}"
    




