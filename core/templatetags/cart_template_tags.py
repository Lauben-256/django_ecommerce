from django import template
from core.models import Order, OrderItem

register = template.Library()  # So we can register our template tag


# @register.filter
# def cart_item_count(user):
#     if user.is_authenticated:
#         qs = OrderItem.objects.filter(user=user, ordered=False)
#         if qs.exists():
#             count = 0
#             for item in qs:
#                 count += item.quantity
#             return count
#         return 0


@register.filter
def cart_item_count(user):  # Function to determine the name of the template library
    if user.is_authenticated:
        qs = Order.objects.filter(user=user, ordered=False)
        if qs.exists():
            return qs[0].items.count()  # Getting the only order in the query set
    return 0
