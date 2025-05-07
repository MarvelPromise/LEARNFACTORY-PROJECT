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
                    return redirect('store')
                else:
                    messages.error(request, 'Password is incorrect!')

            except User.DoesNotExist:
                messages.error(request, 'Email not found!')

        context = {}
        return render(request, 'store/login.html', context)

def logoutUser(request):
    logout(request)
    return redirect('login')

# ========================
# Store Views
# ========================

@login_required(login_url='login')
def store(request):
    products = Product.objects.all()
    context = {'products': products}
    return render(request, 'store/store.html', context)

@login_required(login_url='login')
def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0

    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            total = product.price * quantity
            total_price += total
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total': total
            })
        except Product.DoesNotExist:
            continue

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

@login_required(login_url='login')
def add_to_cart(request, product_id):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'User not logged in'})

        product = Product.objects.get(id=product_id)
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Ensure you're using `cart` here
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        cart_item.quantity += 1
        cart_item.save()

        # Calculate total items in the cart
        total_items = sum(item.quantity for item in cart.items.all())

        return JsonResponse({'success': True, 'message': 'CartItem added', 'cart_count': total_items})

    return JsonResponse({'success': False})




def about_us(request):
    return render(request, 'store/about_us.html')

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



