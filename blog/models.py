from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class BlogPost(models.Model):
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True, blank=True)

    category = models.CharField(
        max_length=80,
        default="Journal",
        help_text="Example: Hair Care, Face Care, Body Care",
    )

    kicker = models.CharField(
        max_length=120,
        blank=True,
        help_text="Example: Hair Care Guide",
    )

    subtitle = models.TextField(blank=True)

    read_time = models.CharField(
        max_length=40,
        blank=True,
        help_text="Example: 7 min read",
    )

    meta_text_1 = models.CharField(
        max_length=180,
        blank=True,
        help_text="Example: Plant-based & sulfate-free formulations",
    )

    meta_text_2 = models.CharField(
        max_length=180,
        blank=True,
        help_text="Example: Zero-plastic packaging on both formats",
    )

    excerpt = models.TextField(
        blank=True,
        help_text="Short description shown on the Blog listing page.",
    )

    content_html = models.TextField(
        help_text=(
            "Paste the article HTML here. Do not include <!DOCTYPE>, "
            "<html>, <head>, <body>, or <style>. Only paste the article content."
        )
    )

    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    seo_title = models.CharField(max_length=220, blank=True)
    meta_description = models.CharField(max_length=320, blank=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 2

            while BlogPost.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog_detail", kwargs={"slug": self.slug})
