from .models import *
from django.contrib import admin, messages
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from django.contrib.auth import get_user_model


class InventoryFilter(admin.SimpleListFilter):
    title = "Critical Inventory Status"
    parameter_name = 'inventory'
    LESS_THAN_3 = '<3'
    BETWEEN_3_AND_10 = '3<=10'
    GREATER_THAN_10 = '>10'

    def lookups(self, request, model_admin):
        return [
            (InventoryFilter.LESS_THAN_3, "High"),
            (InventoryFilter.BETWEEN_3_AND_10, "Medium"),
            (InventoryFilter.GREATER_THAN_10, "Ok"),
        ]

    def queryset(self, request, queryset):
        if self.value() == InventoryFilter.LESS_THAN_3:
            return queryset.filter(inventory__lt=3)
        if self.value() == InventoryFilter.BETWEEN_3_AND_10:
            return queryset.filter(inventory__range=(3, 10))
        if self.value() == InventoryFilter.GREATER_THAN_10:
            return queryset.filter(inventory__gt=10)

        # return super().queryset(request, queryset)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit_price', 'inventory',
                    'datetime_created', 'product_category', 'inventory_is_low', 'comments_count',)
    list_per_page = 10
    list_editable = ("unit_price", "inventory",)
    list_select_related = ('categoy',)
    list_filter = ('datetime_created', InventoryFilter,)
    list_display_links = ('name',)
    actions = ('clear_inventory', )
    search_fields = ('name',)
    prepopulated_fields = {
        'slug': ("name",),
    }

    def get_queryset(self, request):
        queryset = super().get_queryset(request).\
            prefetch_related('comments').\
            annotate(comments_count=Count('comments'))
        return queryset

    @admin.display(description='# comments', ordering='comments_count')
    def comments_count(self, obj):
        # Example: http://127.0.0.1:8000/admin/store/comment/?product__id=97
        url = (
            reverse('admin:store_comment_changelist')
            + '?'
            + urlencode({
                'product__id': obj.id
            })
        )
        return format_html('<a href="{}">{}</a>', url, obj.comments_count)

    @admin.display(ordering='categoy_id')
    def product_category(self, obj: Product):
        try:
            return obj.categoy.name
        except:
            return None

    @admin.action(description='Clear Inventory')
    def clear_inventory(self, request, queryset):
        # queryset: all selected records
        update_count = queryset.update(inventory=0)
        self.message_user(
            request,
            f'{update_count} products have been cleared of inventory.',
            messages.SUCCESS
        )

    def inventory_is_low(self, obj):
        return obj.inventory < 10

    inventory_is_low.boolean = True


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'product')
    autocomplete_fields = ('product',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ('product', 'quantity', 'unit_price')
    extra = 0
    min_num = 1  # The user can't remove all items from the order
    max_num = 10  # The user can't add more than 10 items


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['customer', 'status', 'datetime_created', 'items_count']
    list_editable = ['status']
    list_filter = ['status']
    ordering = ['-datetime_created']
    search_fields = ('customer', )
    inlines = (OrderItemInline, )

    def get_queryset(self, request):
        queryset = super().get_queryset(request).\
            prefetch_related('items').\
            annotate(_items_count=Count("items", distinct=True),
                     )
        return queryset

    # to change the name of column in admin panel
    @admin.display(description='# Items')
    def items_count(self, obj):
        # return obj._items_count
        url = (
            reverse('admin:store_orderitem_changelist')
            + '?'
            + urlencode({
                'order__id': obj.id
            })
        )
        return format_html('<a href="{}">{}</a>', url,  obj._items_count)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'unit_price', 'quantity', )
    autocomplete_fields = ('product',)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email')
    search_fields = ('user__first_name__istartswith', 'user__last_name__istartswith')
    list_per_page = 10
    ordering = ('user__first_name', 'user__last_name')

    def email(self, obj):
        return obj.user.email


class CartItemInline(admin.TabularInline):
    model = CartItem
    fields = ('product', 'quantity')
    extra = 1


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at')
    inlines = (CartItemInline, )
