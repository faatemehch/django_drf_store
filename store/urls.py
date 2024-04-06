from . import views
from django.urls import path, include
from rest_framework_nested import routers


router = routers.DefaultRouter()
router.register('products', views.ProductViewSet, basename='product')
router.register('categories', views.CategoryViewSet, basename='category')
router.register('carts', views.CartViewSet, basename='cart')
router.register('customers', views.CustomerViewSet, basename='customer')
router.register('orders', views.OrderViewSet, basename='order')


product_routers = routers.NestedDefaultRouter(router, 'products', lookup='product')
product_routers.register('comments', views.CommnetViewSet, basename='product-comments')

carts_items_routers = routers.NestedDefaultRouter(router, 'carts', lookup='cart')
carts_items_routers.register('items', views.CartItemViewSet, basename='cart-items')

urlpatterns = router.urls + product_routers.urls + carts_items_routers.urls
# -------------------------
# from rest_framework.routers import SimpleRouter, DefaultRouter
# router = DefaultRouter()
# router.register('products', views.ProductViewSet, basename='product')
# router.register('categories', views.CategoryViewSet, basename='category')

# urlpatterns = router.urls

# urlpatterns = [
#     path('', include(router.urls))
# ]
# -------------------------
# urlpatterns = [
#     path('products/', views.ProductList.as_view()),
#     path('products/<int:pk>/', views.ProductDetail.as_view()),
#     path('categories/', views.CategoryList.as_view()),
#     path('categories/<int:pk>/', views.CategoryDetail.as_view(), name='category-name'),
# ]
