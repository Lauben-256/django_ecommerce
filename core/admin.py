from django.contrib import admin

from .models import Item, OrderItem, Order, Payment, Coupon
# Register your models here.

class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'ordered', 'ordered_date']

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'quantity']

admin.site.register(Item)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)