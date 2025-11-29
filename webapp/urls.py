from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contacts/', views.contacts, name='contacts'),
    path('jobs/', views.jobs, name='jobs'),
    
    # Auth
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Product CRUD
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/update/', views.product_update, name='product_update'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    # Cart
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:pk>/', views.update_cart, name='update_cart'),
    
    # Orders
    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:order_id>/repeat/', views.repeat_order, name='repeat_order'),
    path('orders/<int:order_id>/review/', views.order_review, name='order_review'),
    path('reviews/<int:review_id>/admin-comment/', views.add_admin_comment, name='add_admin_comment'),
    
    # Checkout
    path('checkout/', views.checkout, name='checkout'),
]
