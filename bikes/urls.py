from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('catalog/', views.catalog, name='catalog'),
    path('catalog/<str:cat_type>/', views.catalog, name='catalog_type'),
    path('compare/', views.compare_prices, name='compare'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('buy/<slug:slug>/', views.buy_now, name='buy_now'),
    path('trails/', views.trails, name='trails'),
    path('trails/<int:trail_id>/', views.trail_detail, name='trail_detail'),
    path('stores/', views.stores, name='stores'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/modal/', views.cart_modal_fragment, name='cart_modal'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:product_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/pay/', views.create_payment_session, name='checkout_pay'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),

    path('test/', views.cyclist_test, name='cyclist_test'),
]
