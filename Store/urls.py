# Store/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

        # Your normal pages
    path('', views.store, name="store"),
    path('cart/', views.cart_view, name="cart_view"),
    path('checkout/', views.checkout, name="checkout"),
    path('about_us/', views.about_us, name='about_us'),
    path('product_list/', views.product_list, name='product_list'),
    path('category/<slug:slug>/', views.products_by_category, name='products_by_category'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),




    path('register/', views.registerPage, name="register"),
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),

    # For Admin dashboard
    path('admin-dashboard/', views.admin_dashboard, name="admin-dashboard"),
    path('customer_dashboard/', views.customer_dashboard, name='customer-dashboard'),
    path('profile/', views.profile, name='profile'),

    path('process_order/', views.process_order, name='process_order'),
    path('payment/', views.payment, name='payment'),  # Make sure you have a payment view
    path('confirm_payment/', views.confirm_payment, name='confirm_payment'),

    # For reset password
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
