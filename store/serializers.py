from rest_framework import serializers
import decimal
from .models import Category, Product, Comment, Cart, CartItem, Customer, Order, OrderItem
from django.utils.text import slugify
from django.db import transaction

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ('id', 'user', 'birth_date')
        read_only_fields = ('user', )


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('id', 'name', 'body',)

    def create(self, validate_data):
        product_id = self.context['product_pk']
        return Comment.objects.create(product_id=product_id, **validate_data)


class CategorySerializer(serializers.ModelSerializer):
    # product_count = serializers.SerializerMethodField()
    product_count = serializers.IntegerField(
        source='products.count', read_only=True)

    class Meta:
        model = Category
        fields = ("id", "title", "description", "product_count")

    # def get_product_count(self, obj):
    #     return obj.products.count()
    def validate(self, data):
        if len(data['title']) < 3:
            raise serializers.ValidationError(
                'Title length should be at least 3.')
        return data


class ProductSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=255, source='name')
    price_after_tax = serializers.SerializerMethodField(
        method_name='calculate_tax')
    # category = serializers.HyperlinkedRelatedField(
    #     queryset=Category.objects.all(),
    #     view_name='category-name')

    class Meta:
        model = Product
        fields = ('id', 'title', 'unit_price', "description",
                  'price_after_tax', 'inventory', 'category')

    def calculate_tax(self, obj):
        return round(obj.unit_price * decimal.Decimal(1.09), 2)

    def validate(self, data):
        if len(data['name']) < 6:
            raise serializers.ValidationError(
                "Product Title length Should be at least 6.")
        return data

    def create(self, validate_data):
        product = Product(**validate_data)
        product.slug = slugify(product.name)
        product.save()
        return product


class CartProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'name', 'unit_price')


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ('quantity', )


class AddCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ('id', 'product', 'quantity')

    def create(self, validated_data):
        cart_id = self.context['cart_pk']
        product = validated_data.get('product')
        quantity = validated_data.get('quantity')
        try:
            cart_item = CartItem.objects.get(
                cart_id=cart_id, product_id=product.id)
            cart_item.quantity += quantity
            cart_item.save()
        except CartItem.DoesNotExist:
            cart_item = CartItem.objects.create(
                cart_id=cart_id, **validated_data)
        self.instance = cart_item
        return cart_item


class CartItemSrrializer(serializers.ModelSerializer):
    product = CartProductSerializer()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'quantity', 'total_price')

    def get_total_price(self, obj):
        return obj.product.unit_price * obj.quantity


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSrrializer(many=True, read_only=True)
    cart_total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ('id', 'items', 'cart_total_price')
        read_only_fields = ('id', )

    def get_cart_total_price(self, obj):
        return sum(item.product.unit_price * item.quantity for item in obj.items.all())


class OrderProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'name', 'unit_price')


class OrderItemSerializer(serializers.ModelSerializer):
    product = OrderProductSerializer()

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'quantity', 'unit_price')


class CustomerOrderSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        max_length=255, source='user.first_name')
    last_name = serializers.CharField(max_length=255, source='user.last_name')
    email = serializers.CharField(max_length=255, source='user.email')

    class Meta:
        model = Customer
        fields = ('id', 'first_name', 'last_name', 'email')


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ('id', 'customer', 'status', 'datetime_created', 'items')


class OrderForAdminSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer = CustomerOrderSerializer()

    class Meta:
        model = Order
        fields = ('id', 'customer', 'status', 'datetime_created', 'items')


class OrderCreateSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()

    def validate_cart_id(self, cart_id):
        try:
            if Cart.objects.prefetch_related('items').get(id=cart_id).items.count() == 0:
                raise serializers.ValidationError(
                    'Your cart is empty. Please add a few product to your cart.')
        except Cart.DoesNotExist:
            raise serializers.ValidationError(
                'There is no cart with this cart id')
        return cart_id

        # if not Cart.objects.filter(id=cart_id).exists():
        #     raise serializers.ValidationError('There is no cart with this cart id')
        # if CartItem.objects.filter(cart_id=cart_id).count() == 0:
        #     raise serializers.ValidationError('Your cart is empty. Please add a few product to your cart.')
        # return cart_id

    def save(self, **kwargs):
        with transaction.atomic():
            cart_id = self.validated_data['cart_id']
            user_id = self.context['user_id']
            customer = Customer.objects.get(user_id=user_id)
            cart_items = CartItem.objects.select_related(
                'product').filter(cart_id=cart_id)
            order = Order()
            order.customer = customer
            order.save()
            order_items = [
                OrderItem(
                    order=order,
                    product_id=item.product_id,
                    unit_price=item.product.unit_price,
                    quantity=item.quantity
                ) for item in cart_items]

            OrderItem.objects.bulk_create(order_items)
            Cart.objects.get(pk=cart_id).delete()
            return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('status', )