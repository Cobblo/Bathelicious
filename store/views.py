from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import (
    Product,
    ProductFAQ,
    ReviewRating,
    ProductGallery,
    Wishlist,
    SmallBanner,
    AboutSettings,
    ReviewVideo,
    ComboPageContent,
)

from category.models import Category
from carts.models import CartItem
from carts.views import _cart_id
from .forms import ReviewForm
from orders.models import OrderProduct
from banners.models import Banner


# =========================================================
# HOME
# =========================================================

def home(request):
    featured_products = Product.objects.filter(
        is_featured=True,
        is_available=True
    )[:8]

    new_arrivals = Product.objects.filter(
        is_new_arrival=True,
        is_available=True
    )[:8]

    banners = Banner.objects.all()
    categories = Category.objects.all()

    small_banner = SmallBanner.objects.filter(
        is_active=True
    ).first()

    review_videos = ReviewVideo.objects.filter(
        is_active=True
    ).order_by('order')

    customer_reviews = ReviewRating.objects.filter(
        status=True
    ).select_related(
        'user',
        'product'
    ).order_by('-updated_at')

    context = {
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'banners': banners,
        'categories': categories,
        'small_banner': small_banner,
        'review_videos': review_videos,
        'customer_reviews': customer_reviews,
    }

    return render(
        request,
        'home.html',
        context
    )


# =========================================================
# STORE / CATEGORY
# =========================================================

def store(request, category_slug=None):
    categories = Category.objects.all()
    category = None

    if category_slug:
        category = get_object_or_404(
            Category,
            slug=category_slug
        )

        products = Product.objects.filter(
            category=category,
            is_available=True
        ).order_by('id')

        seo_title = (
            category.seo_title
            if category.seo_title
            else f"{category.category_name} | Bathelicious"
        )

        h1_title = (
            category.h1_title
            if category.h1_title
            else category.category_name
        )

        meta_description = (
            category.meta_description
            if category.meta_description
            else category.description
        )

        primary_keyword = (
            category.primary_keyword
            if category.primary_keyword
            else category.category_name
        )

    else:
        products = Product.objects.filter(
            is_available=True
        ).order_by('id')

        seo_title = (
            "Bathelicious Skincare, Haircare & Body Care Products"
        )

        h1_title = (
            "Skincare, Haircare & Body Care"
        )

        meta_description = (
            "Shop Bathelicious plant-powered skincare, haircare and body care "
            "products designed for everyday nourishment and thoughtful personal care."
        )

        primary_keyword = (
            "plant based skincare"
        )

    paginator = Paginator(
        products,
        8
    )

    page = request.GET.get(
        'page'
    )

    paged_products = paginator.get_page(
        page
    )

    product_count = products.count()

    context = {
        'products': paged_products,
        'product_count': product_count,
        'links': categories,
        'category': category,

        # SEO
        'seo_title': seo_title,
        'h1_title': h1_title,
        'meta_description': meta_description,
        'primary_keyword': primary_keyword,
    }

    return render(
        request,
        'store/store.html',
        context
    )


# =========================================================
# PRODUCT DETAIL
# =========================================================

def product_detail(
    request,
    category_slug,
    product_slug
):
    single_product = get_object_or_404(
        Product,
        category__slug=category_slug,
        slug=product_slug
    )

    in_cart = CartItem.objects.filter(
        cart__cart_id=_cart_id(request),
        product=single_product
    ).exists()

    orderproduct = None

    if request.user.is_authenticated:
        orderproduct = OrderProduct.objects.filter(
            user=request.user,
            product=single_product
        ).exists()

        in_wishlist = Wishlist.objects.filter(
            user=request.user,
            product=single_product
        ).exists()

    else:
        in_wishlist = False

    reviews = ReviewRating.objects.filter(
        product_id=single_product.id,
        status=True
    )

    product_gallery = ProductGallery.objects.filter(
        product_id=single_product.id
    )

    faqs = ProductFAQ.objects.filter(
        product=single_product,
        is_active=True
    ).order_by('order')[:10]

    related_products = single_product.related_products.filter(
        is_available=True
    ).exclude(
        id=single_product.id
    )[:4]

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
        'in_wishlist': in_wishlist,
        'faqs': faqs,
        'related_products': related_products,
    }

    return render(
        request,
        'store/product_detail.html',
        context
    )


# =========================================================
# OLD URL 301 REDIRECTS
# =========================================================

def old_category_redirect(
    request,
    category_slug
):
    """
    Permanently redirect old category URLs:

    /store/category/face-care/

    to:

    /store/face-care/
    """

    category = get_object_or_404(
        Category,
        slug=category_slug
    )

    return redirect(
        'products_by_category',
        category_slug=category.slug,
        permanent=True
    )


def old_product_redirect(
    request,
    category_slug,
    product_slug
):
    """
    Permanently redirect old product URLs:

    /store/category/face-care/product-name/

    to:

    /store/face-care/product-name/
    """

    product = get_object_or_404(
        Product,
        category__slug=category_slug,
        slug=product_slug
    )

    return redirect(
        'product_detail',
        category_slug=product.category.slug,
        product_slug=product.slug,
        permanent=True
    )


# =========================================================
# SEARCH
# =========================================================

def search(request):
    products = Product.objects.none()
    product_count = 0

    keyword = request.GET.get(
        'keyword'
    )

    if keyword:
        products = Product.objects.filter(
            Q(description__icontains=keyword) |
            Q(product_name__icontains=keyword),
            is_available=True
        ).order_by('-created_date')

        product_count = products.count()

    paginator = Paginator(
        products,
        8
    )

    page = request.GET.get(
        'page'
    )

    paged_products = paginator.get_page(
        page
    )

    context = {
        'products': paged_products,
        'product_count': product_count,
        'links': Category.objects.all(),

        # SEO
        'seo_title': (
            "Search Products | Bathelicious"
        ),

        'h1_title': (
            "Search Products"
        ),

        'meta_description': (
            "Search Bathelicious skincare, haircare and body care products."
        ),
    }

    return render(
        request,
        'store/store.html',
        context
    )


# =========================================================
# WISHLIST
# =========================================================

@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(
        user=request.user
    )

    return render(
        request,
        'store/wishlist.html',
        {
            'wishlist_items': wishlist_items
        }
    )


@login_required
def add_to_wishlist(
    request,
    product_id
):
    product = get_object_or_404(
        Product,
        id=product_id
    )

    Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    return redirect(
        'wishlist'
    )


@login_required
def remove_from_wishlist(
    request,
    product_id
):
    product = get_object_or_404(
        Product,
        id=product_id
    )

    Wishlist.objects.filter(
        user=request.user,
        product=product
    ).delete()

    return redirect(
        'wishlist'
    )


# =========================================================
# REVIEWS
# =========================================================

def submit_review(
    request,
    product_id
):
    url = request.META.get(
        'HTTP_REFERER',
        '/'
    )

    if request.method == 'POST':
        try:
            review = ReviewRating.objects.get(
                user_id=request.user.id,
                product_id=product_id
            )

            form = ReviewForm(
                request.POST,
                instance=review
            )

            if form.is_valid():
                form.save()

                messages.success(
                    request,
                    'Thank you! Your review has been updated.'
                )

        except ReviewRating.DoesNotExist:
            form = ReviewForm(
                request.POST
            )

            if form.is_valid():
                data = ReviewRating(
                    subject=form.cleaned_data.get(
                        'subject',
                        ''
                    ),
                    rating=form.cleaned_data[
                        'rating'
                    ],
                    review=form.cleaned_data[
                        'review'
                    ],
                    ip=request.META.get(
                        'REMOTE_ADDR'
                    ),
                    product_id=product_id,
                    user_id=request.user.id
                )

                data.save()

                messages.success(
                    request,
                    'Thank you! Your review has been submitted.'
                )

    return redirect(
        url
    )


# =========================================================
# POLICY PAGES
# =========================================================

def shipping_policy(request):
    return render(
        request,
        'store/shipping_policy.html'
    )


def terms_and_conditions(request):
    return render(
        request,
        'store/terms_and_conditions.html'
    )


def privacy_policy(request):
    return render(
        request,
        'store/privacy_policy.html'
    )


def return_and_refund(request):
    return render(
        request,
        'store/return_and_refund.html'
    )


# =========================================================
# COMBOS
# =========================================================

def combos_view(request):
    combo_products = Product.objects.filter(
        is_combo=True,
        is_available=True
    ).order_by('-created_date')

    paginator = Paginator(
        combo_products,
        8
    )

    page = request.GET.get(
        'page'
    )

    combos = paginator.get_page(
        page
    )

    combo_page_content = ComboPageContent.objects.first()

    context = {
        'combos': combos,
        'combo_page_content': combo_page_content,
    }

    return render(
        request,
        'store/combos.html',
        context
    )


# =========================================================
# BESTSELLERS
# =========================================================

def bestsellers_view(request):
    bestsellers = Product.objects.filter(
        is_bestseller=True,
        is_available=True
    )

    return render(
        request,
        'store/bestsellers.html',
        {
            'bestsellers': bestsellers
        }
    )


# =========================================================
# ABOUT US
# =========================================================

def aboutus(request):
    about = AboutSettings.objects.first()

    return render(
        request,
        'store/about_us.html',
        {
            'about': about
        }
    )