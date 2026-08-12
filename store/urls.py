from django.urls import path
from . import views


urlpatterns = [

    # =====================================================
    # STORE HOME
    # =====================================================

    path(
        '',
        views.store,
        name='store'
    ),


    # =====================================================
    # SEARCH
    # =====================================================

    path(
        'search/',
        views.search,
        name='search'
    ),


    # =====================================================
    # REVIEWS
    # =====================================================

    path(
        'submit_review/<int:product_id>/',
        views.submit_review,
        name='submit_review'
    ),


    # =====================================================
    # WISHLIST
    # =====================================================

    path(
        'wishlist/',
        views.wishlist,
        name='wishlist'
    ),

    path(
        'wishlist/add/<int:product_id>/',
        views.add_to_wishlist,
        name='add_to_wishlist'
    ),

    path(
        'wishlist/remove/<int:product_id>/',
        views.remove_from_wishlist,
        name='remove_from_wishlist'
    ),


    # =====================================================
    # COMBOS
    # =====================================================

    path(
        'combos/',
        views.combos_view,
        name='combos'
    ),


    # =====================================================
    # BESTSELLERS
    # =====================================================

    path(
        'bestsellers/',
        views.bestsellers_view,
        name='bestsellers'
    ),


    # =====================================================
    # ABOUT US
    # =====================================================

    path(
        'aboutus/',
        views.aboutus,
        name='aboutus'
    ),


    # =====================================================
    # OLD URLS
    # 301 REDIRECT TO NEW SEO URLS
    # =====================================================

    # OLD:
    # /store/category/face-care/
    #
    # REDIRECTS TO:
    # /store/face-care/

    path(
        'category/<slug:category_slug>/',
        views.old_category_redirect,
        name='old_products_by_category'
    ),


    # OLD:
    # /store/category/face-care/product-name/
    #
    # REDIRECTS TO:
    # /store/face-care/product-name/

    path(
        'category/<slug:category_slug>/<slug:product_slug>/',
        views.old_product_redirect,
        name='old_product_detail'
    ),


    # =====================================================
    # NEW SEO PRODUCT URL
    # =====================================================

    # Example:
    # /store/face-care/skin-revitalise-night-cream/

    path(
        '<slug:category_slug>/<slug:product_slug>/',
        views.product_detail,
        name='product_detail'
    ),


    # =====================================================
    # NEW SEO CATEGORY URL
    # =====================================================

    # Example:
    # /store/face-care/

    path(
        '<slug:category_slug>/',
        views.store,
        name='products_by_category'
    ),

]