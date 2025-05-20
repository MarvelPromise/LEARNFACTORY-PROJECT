from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# from .forms import CreateUserForm   # Import your form
from .forms import CustomUserCreationForm
from django.shortcuts import get_object_or_404
from .models import Product, CartItem, Cart
from django.http import JsonResponse
import json
from .models import *

# ========================
# Authentication Views
# ========================

def registerPage(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'store/register.html', {'form': form})

def loginPage(request):
    if request.user.is_authenticated:
        return redirect('store')
    else:
        if request.method == 'POST':
            email = request.POST.get('email')
            password = request.POST.get('password')

            try:
                user_obj = User.objects.get(email=email)
                username = user_obj.username
                user = authenticate(request, username=username, password=password)

                if user is not None:
                    login(request, user)
                    return redirect('Store')
                else:
                    messages.error(request, 'Password is incorrect!')

            except User.DoesNotExist:
                messages.error(request, 'Email not found!')

        context = {}
        return render(request, 'store/login.html', context)

def logoutUser(request):
    logout(request)
    return redirect('login')

# =========================================== # Store Views # ==========================================================

@login_required(login_url='login')
def store(request):

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
		items = order.orderitem_set.all()
		cartItems = order.orderitem_set.all()
	else:
		#Create empty cart for now for non-logged in user
		items = []
		order = {'get_cart_total':0, 'get_cart_items':0}
		cartItems = order['get_cart_items']

	products = Product.objects.all()
	context = {'products':products, 'cartItems':cartItems}
	return render(request, 'store/store.html', context)

def cart(request, product_id):
    product = Product.objects.get(pk=product_id)
    cart = request.session.get('cart', {})
    cart_item = cart.get(product_id)

    if cart_item:
        cart_item['quantity'] += 1
    else:
        cart_item = {'quantity': 1, 'product': product}

    cart[product_id] = cart_item
    request.sessional
@login_required(login_url='login')
def cart_view(request):
    # Get or create the cart for the logged-in user
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Get all cart items for that cart
    cart_items = CartItem.objects.filter(cart=cart)
    total_price = 0
    
    # Loop through each cart item to calculate total price
    for item in cart_items:
        total_price += item.product.price * item.quantity
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }

    return render(request, 'store/cart.html', context)

@login_required(login_url='login')
def checkout(request):
    customer = request.user.customer
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    items = order.orderitem_set.all()

    if request.method == 'POST':
        # Collect the checkout data (e.g., address and payment method)
        address = request.POST.get('address')
        payment_method = request.POST.get('payment_method')

        # Redirect to process order view with the collected data
        return redirect('process_order')  # Redirect to process_order to save data and handle payment

    context = {'items': items, 'order': order}
    return render(request, 'store/checkout.html', context)
    

@login_required(login_url='login')
def admin_dashboard(request):
    products = Product.objects.all()
    orders = Order.objects.all()
    customers = Customer.objects.all()

    total_products = products.count()
    total_orders = orders.count()
    total_customers = customers.count()
    total_revenue = sum([order.get_cart_total for order in orders if order.complete])

    recent_orders = orders.order_by('-date_ordered')[:5]  # Latest 5 orders

    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
    }
    return render(request, 'store/admin_dashboard.html', context)

@login_required(login_url='login')
def process_order(request):
    if request.method == 'POST':
        address = request.POST.get('address')
        payment_method = request.POST.get('payment_method')

        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)

        # Save address and payment
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=address,
            payment_method=payment_method
        )

        # Mark order as complete
        order.complete = True
        order.save()

        if payment_method in ['card', 'paypal']:
            request.session['payment_method'] = payment_method
            return redirect('payment')

        messages.success(request, "Order placed successfully!")
        return redirect('store')

    return redirect('checkout')

@login_required(login_url='login')
def payment(request):
    payment_method = request.session.get('payment_method')

    if payment_method == 'card':
        # Handle card payment form
        return render(request, 'store/card_payment.html')
    elif payment_method == 'paypal':
        # Handle PayPal payment
        return render(request, 'store/paypal_payment.html')
    else:
        # Invalid payment method or fallback
        return redirect('store')
    
@login_required(login_url='login')
def confirm_payment(request):
    messages.success(request, "Payment confirmed and order completed!")
    return redirect('store')

@login_required(login_url='login')
def profile(request):
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        customer = None  # Or create a new one if needed

    context = {
        'customer': customer,
    }
    return render(request, 'store/profile.html', context)


@login_required(login_url='login')
def customer_dashboard(request):
    orders = Order.objects.filter(customer__user=request.user).order_by('-date_ordered')[:5]
    return render(request, 'store/customer_dashboard.html', {'orders': orders})

def category_products(request, slug):
    category = Category.objects.get(slug=slug)
    products = Product.objects.filter(category=category)
    return render(request, 'store/category_products.html', {
        'category': category,
        'products': products
    })

def product_list(request):
    category_slug = request.GET.get('category')
    products = Product.objects.all()
    categories = Category.objects.all()

    if category_slug:
        products = products.filter(category__slug=category_slug)

    context = {
        'products': products,
        'categories': categories,
        'active_category': category_slug
    }
    return render(request, 'store/product_list.html', context)
# @login_required(login_url='login')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Retrieve cart (e.g., via session or user)
    cart_id = request.session.get("cart_id")
    if not cart_id:
        cart = Cart.objects.create()
        request.session["cart_id"] = cart.id
    else:
        cart = Cart.objects.get(id=cart_id)

    # Check if item already in cart
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()

    return redirect("cart_view")  # or return JsonResponse if using JS


def updateItem(request):
	data = json.loads(request.body)
	productId = data['productId']
	action = data['action']
	print('Action:', action)
	print('Product:', productId)

	customer = request.user.customer
	product = Product.objects.get(id=productId)
	order, created = Order.objects.get_or_create(customer=customer, complete=False)

	orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

	if action == 'add':
		orderItem.quantity = (orderItem.quantity + 1)
	elif action == 'remove':
		orderItem.quantity = (orderItem.quantity - 1)

	orderItem.save()

	if orderItem.quantity <= 0:
		orderItem.delete()

	return JsonResponse('Item was added', safe=False)

def main(request):
    return render(request, 'store/main.html')
def about_us(request):
    return render(request, 'store/about_us.html')

def contact_us(request):
    return render(request, 'store/contact.html')

def FAQs(request):
    return render(request, 'store/faqs.html')

def Store(request):
    return render( request, 'store/store.html')
def Policies(request):
    return render(request, 'store/policieshome.html')
def products_by_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    return render(request, 'store/products_by_category.html', {
        'category': category,
        'products': products
    })

@login_required(login_url='login')
def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        cart_item = CartItem.objects.get(user=request.user, product=product)
        cart_item.delete()
        messages.success(request, "Item removed from cart.")
    except CartItem.DoesNotExist:
        messages.error(request, "Item not found in cart.")
    return redirect('cart')



############################ Policies #############################
def customerservicepolicy(request):
    return render(request, 'Policies/customerservicepolicy.html')

def intellectualpropertynpolicy(request):
    return render(request, 'intellectualpropertynpolicy.html')

def ordercancellationpolicy(request):
    return render(request, 'Policies/ordercancellationpolicy.html')
def paymentpolicy(request): 
    return render(request, 'Policies/paymentpolicy.html')
def privacypolicy(request):
    return render(request, 'Policies/privacypolicy.html')
def returnrefundpolicy(request):
    return render(request, 'Policies/ReturnRefundpolicy.html')
def productwarranty(request):
    return render(request, 'Policies/productwarranty.html')
def shippingpolicy(request):
    return render(request, 'Policies/shippingpolicy.html')

###################################### Fragrance category #####################################################
def bodyspray(request):
    return render(request,'category/Body Spray.html')
def Fragrance(request):
    return render(request, 'category/fragrance.html')

def Footwear(request):
    return render(request, 'category/shoes.html')
def watch(request):
    return render(request, 'category/watches.html')
def jewelry(request):
    return render(request, 'category/necklace.html')
def roll_on(request):
    return render(request, 'category/Roll-on.html')

def perfume(request):
    return render(request, 'category/perfume.html')