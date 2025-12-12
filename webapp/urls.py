from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contacts/', views.contacts, name='contacts'),
    path('jobs/', views.jobs, name='jobs'),
    path('legal/', views.legal, name='legal'),
    path('delivery-payment/', views.delivery_payment, name='delivery_payment'),
    
    # Auth
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    
    # Product CRUD
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/update/', views.product_update, name='product_update'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    # Cart
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:pk>/', views.update_cart, name='update_cart'),
    path('cart/update_item/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove_item/', views.remove_cart_item, name='remove_cart_item'),
    path('api/cart-count/', views.cart_count_api, name='cart_count_api'),
    
    # Orders
    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:order_id>/repeat/', views.repeat_order, name='repeat_order'),
    path('orders/<int:order_id>/review/', views.order_review, name='order_review'),
    path('reviews/<int:review_id>/admin-comment/', views.add_admin_comment, name='add_admin_comment'),
    
    # Checkout
    path('checkout/', views.checkout, name='checkout'),
    path('api/check-promo/', views.check_promo_code, name='check_promo_code'),
    path('api/cart-total/', views.cart_total_api, name='cart_total_api'),
    
    # Support / Chat
    path('support/', views.support, name='support'),
    path('chat/create/', views.chat_create, name='chat_create'),
    path('chat/<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('chat/<int:chat_id>/messages/', views.chat_messages, name='chat_messages'),
    path('chat/<int:chat_id>/send/', views.chat_send, name='chat_send'),
    path('chat/<int:chat_id>/operator-join/', views.chat_operator_join, name='chat_operator_join'),
]
