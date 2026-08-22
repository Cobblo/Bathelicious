from django.contrib import admin
from django import forms
from .models import BlogPost


class BlogPostAdminForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = "__all__"

        widgets = {
            "subtitle": forms.Textarea(
                attrs={
                    "rows": 3,
                }
            ),

            "excerpt": forms.Textarea(
                attrs={
                    "rows": 4,
                }
            ),

            "content_html": forms.Textarea(
                attrs={
                    "rows": 28,
                    "style": "font-family: monospace; font-size: 13px;",
                }
            ),

            "meta_description": forms.Textarea(
                attrs={
                    "rows": 3,
                }
            ),
        }


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):

    form = BlogPostAdminForm

    # ==============================
    # SHOW SAVE BUTTON AT TOP
    # ==============================

    save_on_top = True


    # ==============================
    # BLOG LIST
    # ==============================

    list_display = (
        "title",
        "category",
        "is_published",
        "published_at",
        "updated_at",
    )

    list_filter = (
        "is_published",
        "category",
        "published_at",
    )

    search_fields = (
        "title",
        "subtitle",
        "excerpt",
        "content_html",
    )

    prepopulated_fields = {
        "slug": ("title",)
    }

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-published_at",
        "-created_at",
    )


    # ==============================
    # ADMIN FORM
    # ==============================

    fieldsets = (

        # PUBLISH SETTINGS FIRST
        (
            "Publishing",
            {
                "fields": (
                    "is_published",
                    "published_at",
                )
            },
        ),

        # BLOG DETAILS
        (
            "Blog",
            {
                "fields": (
                    "title",
                    "slug",
                    "category",
                    "kicker",
                    "subtitle",
                    "read_time",
                    "meta_text_1",
                    "meta_text_2",
                    "excerpt",
                    "content_html",
                )
            },
        ),

        # SEO
        (
            "SEO",
            {
                "classes": (
                    "collapse",
                ),

                "fields": (
                    "seo_title",
                    "meta_description",
                ),
            },
        ),

        # SYSTEM INFO
        (
            "System",
            {
                "classes": (
                    "collapse",
                ),

                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )