from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
import stripe
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import ListView, DetailView, View
from django.conf import settings
from .forms import CheckoutForm
from .models import Item, Order, OrderItem, BillingAddress, Payment

# Create your views here.
stripe.api_key = 'sk_test_51IMnLHFTiAaBFtb8PqOxEN9D03gOTgz2ZQva6PmNhqf39ubmb5mSb7kG0idath9r99YpaKhrH6Zk6p6oObkE9d9n00m3H3o3qG'

class HomeView(ListView):
    model = Item
    paginate_by = 10
    template_name = 'home.html'
    ordering = ['id']

# def home(request):
    # context = {'items': Item.objects.all()}
    # return render(request, 'home.html', context)


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request, "You don't have active order.")
            return redirect('/')


class CheckoutView(View):
    def get(self, *args, **kwargs):
        # form
        form = CheckoutForm()
        context = {
            'form': form
        }
        return render(self.request, "checkout.html", context)

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')
                # TODO: add functionality for these fields
                # same_shipping_address = form.cleaned_data.get('same_billing_address')
                # save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')
                billing_address = BillingAddress(
                    user=self.request.user,
                    street_address=street_address,
                    apartment_address=apartment_address,
                    country=country,
                    zip=zip,
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()
                # TODO add redirect to the selected payment option
                return redirect('core:checkout')
            messages.warning(self.request, "Failed checkout")
            return redirect('core:checkout')
        except ObjectDoesNotExist:
            messages.error(self.request, "You don't have active order.")
            return redirect('core:order-summary')


class PaymentView(View):
    def get(self, *args, **kwargs):
        #order 
        return render(self.request, 'payment.html')

    def post(self, *args, **kwargs):

        # `source` is obtained with Stripe.js; see https://stripe.com/docs/payments/accept-a-payment-charges#web-create-token
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        amount=int(order.get_total() * 100), # cents

        try:
            # Use Stripe's library to make requests...
            charge = stripe.Charge.create(
                    amount=amount,
                    currency="usd",
                    source=token,
                    description="My First Test Charge (created for API docs)",
                )

            # create the payment
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total()
            payment.save()

            # assign the payment to the order
            order.ordered = True
            order.payment = payment
            order.save()
            messages.success(self.request, "Your order was successful!.")
            return redirect('/')

        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            body = e.json_body
            err = body.get('error', {})
            messages.error(self.request, f"{err.get('message')}")
            return redirect('/')

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.error(self.request, "Rate Limit Error")
            return redirect('/')

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.error(self.request, "Invalid Parameters.")
            return redirect('/')

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.error(self.request, "Not Authenticated.")
            return redirect('/')

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.error(self.request, "Network Error.")
            return redirect('/')

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.error(self.request, "Something went wrong. You were not charged. Please try again.")
            return redirect('/')

        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            # Send an email to ourselves

            messages.error(self.request, "A serious error occurred. We have been notified.")
            return redirect('/')

class ItemDetailView(DetailView):
    model = Item
    template_name = 'product.html'


# def products(request):
    # context = {'items': Item.objects.all()}
    # return render(request, 'products.html', context)

@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(item=item, user=request.user, ordered=False)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # Check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was added to your cart.")
            order.items.add(order_item)
            return redirect("core:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item quantity was updated.")
    return redirect("core:order-summary")


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # Check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(item=item, user=request.user, ordered=False)[0]
            order_item.quantity = 1
            order.items.remove(order_item)
            order_item.save()
            messages.info(request, "This item was removed from your cart.")
            return redirect('core:order-summary')
        else:
            messages.info(request, "This item was not in your cart.")
            # Add a messag saying the order doesn't contain this order item
            return redirect('core:product', slug=slug)
    else:
        # Add a message saying the user doesn't have an order
        messages.info(request, "You do not have an order.")
        return redirect('core:product', slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # Check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(item=item, user=request.user, ordered=False)[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated.")
            return redirect('core:order-summary')
        else:
            messages.info(request, "This item was not in your cart.")
            # Add a messag saying the order doesn't contain this order item
            return redirect('core:product', slug=slug)
    else:
        # Add a message saying the user doesn't have an order
        messages.info(request, "You do not have an order.")
        return redirect('core:product', slug=slug)
