from .filters import ProductFilter
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny, DjangoModelPermissions
from .permissions import IsAdminOrReadOnly, SendPrivateEmailToCustomerPermission
from .models import Product, Category, Comment, Cart, CartItem, Customer, Order, OrderItem
from django.db.models import Prefetch
from .signals import order_created
from .paginations import DefaultPagination
from .serializers import (ProductSerializer,
                          CategorySerializer,
                          CommentSerializer,
                          CartSerializer,
                          CartItemSrrializer,
                          AddCartItemSerializer,
                          UpdateCartItemSerializer,
                          CustomerSerializer, OrderItemSerializer, OrderSerializer, OrderForAdminSerializer, OrderCreateSerializer, OrderUpdateSerializer)
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, DestroyModelMixin
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.pagination import PageNumberPagination
# ------------------------- Class Base ModelViewSet -------------------------


class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    filter_backends = (SearchFilter, DjangoFilterBackend, OrderingFilter, )
    ordering_fields = ('name', 'inventory')
    search_fields = ('name', 'category__title')
    pagination_class = DefaultPagination
    # filterset_fields = ('category_id', 'inventory')
    filterset_class = ProductFilter
    queryset = Product.objects.all()

    def get_serializer_context(self):
        return {'request': self.request}

    def destroy(self, request, pk):
        product = get_object_or_404(
            Product.objects.select_related('category'), pk=pk)
        if product.order_items.count() > 0:
            return Response({'error': 'There are some order items related to this product'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.prefetch_related('products').all()
    permission_classes = (IsAdminOrReadOnly,)

    def delete(self, request, pk):
        category = get_object_or_404(
            Category.objects.annotate(product_count=Count('products')), pk=pk)
        if category.products.count() > 0:
            return Response({'error': 'There are some products related to this category'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommnetViewSet(ModelViewSet):
    serializer_class = CommentSerializer

    def get_queryset(self):
        product_pk = self.kwargs['product_pk']
        return Comment.objects.filter(product_id=product_pk)

    def get_serializer_context(self):
        return {'product_pk': self.kwargs['product_pk']}


class CartItemViewSet(ModelViewSet):
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_queryset(self):
        cart_id = self.kwargs['cart_pk']
        return CartItem.objects.select_related('product').filter(cart_id=cart_id)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return UpdateCartItemSerializer
        return CartItemSrrializer

    def get_serializer_context(self):
        return {'cart_pk': self.kwargs['cart_pk']}


class CartViewSet(CreateModelMixin,
                  RetrieveModelMixin,
                  DestroyModelMixin,
                  GenericViewSet):
    serializer_class = CartSerializer
    queryset = Cart.objects.prefetch_related('items__product').all()
    lookup_value_regex = '[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}'


class CustomerViewSet(ModelViewSet):
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()
    permission_classes = (IsAdminUser, )

    @action(detail=False, methods=('GET', 'PUT'), permission_classes=(IsAuthenticated,))
    def me(self, request):
        user_id = request.user.id
        customer = Customer.objects.get(user_id=user_id)
        if request.method == "GET":
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == "PUT":
            serializer = CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(detail=True, permission_classes=(SendPrivateEmailToCustomerPermission,))
    def send_private_email(self, request, pk):
        return Response(f'Sending Email to customer {pk=}')


class OrderViewSet(ModelViewSet):
    # permission_classes = [IsAuthenticated]
    http_method_names = ('get', 'post', 'patch', 'delete', 'option', 'head')

    def get_permissions(self):  # return object of classes
        if self.request.method in ['PATCH', 'DELETE']:
            return (IsAdminUser(),)
        return (IsAuthenticated(),)

    def get_queryset(self):
        qs = Order.objects.prefetch_related(
            Prefetch(
                'items', queryset=OrderItem.objects.select_related('product')
            )).select_related('customer__user')
        user = self.request.user
        if user.is_staff:
            return qs
        return qs.filter(customer__user_id=user.id)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderCreateSerializer
        if self.request.method == 'PATCH':
            return OrderUpdateSerializer
        if self.request.user.is_staff:
            return OrderForAdminSerializer
        return OrderSerializer

    def get_serializer_context(self):
        return {'user_id': self.request.user.id}

    def create(self, request, *args, **kwargs):
        create_order_serializer = OrderCreateSerializer(
            data=request.data, context={'user_id': self.request.user.id})
        create_order_serializer.is_valid(raise_exception=True)
        created_order = create_order_serializer.save()

        order_created.send_robust(self.__class__, order=created_order)

        serializer = OrderSerializer(created_order)
        return Response(serializer.data)


# ------------------------- Class Base Mixin Views -------------------------

# class ProductList(ListCreateAPIView):
#     serializer_class = ProductSerializer
#     queryset = Product.objects.select_related('category').all()

#     def get_serializer_context(self):
#         return {'request': self.request}


# class ProductDetail(RetrieveUpdateDestroyAPIView):
#     serializer_class = ProductSerializer
#     queryset = Product.objects.select_related('category').all()
#     lookup_field = 'id'

#     def delete(self, request, id):
#         product = get_object_or_404(
#             Product.objects.select_related('category'), pk=id)
#         if product.order_items.count() > 0:
#             return Response({'error': 'There are some order items related to this product'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
#         product.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


# class CategoryList(ListCreateAPIView):
#     serializer_class = CategorySerializer
#     queryset = Category.objects.prefetch_related('products').all()


# class CategoryDetail(RetrieveUpdateDestroyAPIView):
#     serializer_class = CategorySerializer
#     queryset = Category.objects.annotate(product_count=Count('products'))

#     def delete(self, request, pk):
#         category = get_object_or_404(
#             Category.objects.annotate(product_count=Count('products')), pk=pk)
#         if category.products.count() > 0:
#             return Response({'error': 'There are some products related to this category'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
#         category.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


# ------------------------- Class Base Views -------------------------
# class ProductList(APIView):
#     def get(self, request):
#         qs = Product.objects.select_related('category').all()
#         serializer = ProductSerializer(
#             qs, many=True, context={'request': request})
#         return Response(serializer.data)

#     def post(self, request):
#         serializer = ProductSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response('Done!', status=status.HTTP_201_CREATED)


# class ProductDetail(APIView):
#     def get_object(self, pk):
#         product = get_object_or_404(
#             Product.objects.select_related('category'), pk=pk)
#         return product

#     def get(self, request, pk):
#         product = self.get_object(pk)
#         serializer = ProductSerializer(product, context={'request': request})
#         return Response(serializer.data)

#     def put(self, request, pk):
#         product = self.get_object(pk)
#         serializer = ProductSerializer(product, data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)

#     def delete(self, request, pk):
#         product = self.get_object(pk)
#         if product.order_items.count() > 0:
#             return Response({'error': 'There are some order items related to this product'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
#         product.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


# class CategoryList(APIView):
#     def get(self, request):
#         qs = Category.objects.prefetch_related('products').all()
#         serializer = CategorySerializer(qs, many=True)
#         return Response(serializer.data)

#     def post(self, request):
#         serializer = CategorySerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)


# class CategoryDetail(APIView):
#     def get_object(self, pk):
#         category = get_object_or_404(
#             Category.objects.annotate(product_count=Count('products')), pk=pk)
#         return category

#     def get(self, request, pk):
#         category = self.get_object(pk)
#         serializer = CategorySerializer(category)
#         return Response(serializer.data)

#     def put(self, request, pk):
#         category = self.get_object(pk)
#         serializer = CategorySerializer(category, data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response("Data has been updated.")

#     def delete(self, request, pk):
#         category = self.get_object(pk)
#         if category.products.count() > 0:
#             return Response({'error': 'There are some products related to this category'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
#         category.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)

# ------------------------- Function Base Views -------------------------

# @api_view(['GET', 'POST'])
# def product_list(request):
#     if request.method == 'GET':
#         qs = Product.objects.select_related('category').all()
#         serializer = ProductSerializer(
#             qs, many=True, context={'request': request})
#         return Response(serializer.data)
#     elif request.method == 'POST':
#         serializer = ProductSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response('Done!', status=status.HTTP_201_CREATED)


# @api_view(['GET', "PUT", "DELETE"])
# def product_detail(request, pk):
#     product = get_object_or_404(
#         Product.objects.select_related('category'), pk=pk)
#     if request.method == "GET":
#         serializer = ProductSerializer(product, context={'request': request})
#         return Response(serializer.data)
#     elif request.method == "PUT":
#         serializer = ProductSerializer(product, data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)
#     elif request.method == "DELETE":
#         if product.order_items.count() > 0:
#             return Response({'error': 'There are some order items related to this product'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
#         product.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


# @api_view(["GET", "POST"])
# def category_list(request):
#     if request.method == "GET":
#         qs = Category.objects.annotate(product_count=Count('products')).all()
#         serializer = CategorySerializer(qs, many=True)
#         return Response(serializer.data)
#     elif request.method == "POST":
#         serializer = CategorySerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response('Done!', status=status.HTTP_201_CREATED)


# @api_view(['GET', "PUT", "DELETE"])
# def category_detail(request, pk):
#     category = get_object_or_404(
#         Category.objects.annotate(product_count=Count('products')), pk=pk)
#     if request.method == "GET":
#         serializer = CategorySerializer(category)
#         return Response(serializer.data)
#     elif request.method == "PUT":
#         serializer = CategorySerializer(category, data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response("Data has been updated.")
#     elif request.method == "DELETE":
#         if category.products.count() > 0:
#             return Response({'error': 'There are some products related to this category'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
#         category.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)
