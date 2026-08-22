from django.db import models
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import BlogPost


def blog_list(request):
    posts = BlogPost.objects.filter(
        is_published=True
    ).filter(
        models.Q(published_at__lte=timezone.now()) |
        models.Q(published_at__isnull=True)
    )

    return render(
        request,
        "blog/blog_list.html",
        {"posts": posts},
    )


def blog_detail(request, slug):
    post = get_object_or_404(
        BlogPost,
        slug=slug,
        is_published=True,
    )

    if post.published_at and post.published_at > timezone.now():
        raise Http404("Blog post not found.")

    return render(
        request,
        "blog/blog_detail.html",
        {"post": post},
    )
