from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Min, Max, Count, Case, When, IntegerField
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
import re

from .forms import RegisterForm, LoginForm, UserForm, UserProfileForm, ReviewForm, RidePostForm
from .decorators import login_required_with_message
from chat.models import AIChatRecord
from .models import (
    Category,
    Product,
    Brand,
    Trail,
    Store,
    StoreLocation,
    UserProfile,
    Order,
    OrderItem,
    RidePost,
    RideRequest,
    UserSubscription,
)
from .services import get_product_suggestions, get_suggested_bikes_for_trail, get_suggested_trails_for_bike
from .services import can_create_post, can_send_request, is_premium
from .cart import add_to_cart, cart_lines, cart_total, remove_from_cart, set_qty

# Старі URL /catalog/mens/, /catalog/womens/ → нові типи
BIKE_TYPE_LEGACY = {'mens': 'road', 'womens': 'gravel'}


def home(request):
    featured_bikes = Product.objects.filter(is_featured=True, category__category_type='bike')[:6]
    new_arrivals = Product.objects.filter(is_new=True)[:8]
    bike_categories = Category.objects.filter(category_type='bike')
    gear_categories = Category.objects.filter(category_type='gear')
    popular_trails = Trail.objects.order_by('-rating')[:3]
    brands = Brand.objects.all()[:8]

    cheapest_bike = Product.objects.filter(
        category__category_type='bike', in_stock=True
    ).order_by('price').first()

    site_stats = {
        'products_total': Product.objects.filter(in_stock=True).count(),
        'bikes_count': Product.objects.filter(category__category_type='bike', in_stock=True).count(),
        'trails_count': Trail.objects.count(),
        'brands_count': Brand.objects.count(),
    }

    context = {
        'featured_bikes': featured_bikes,
        'new_arrivals': new_arrivals,
        'bike_categories': bike_categories,
        'gear_categories': gear_categories,
        'popular_trails': popular_trails,
        'brands': brands,
        'site_stats': site_stats,
        'cheapest_bike': cheapest_bike,
    }
    return render(request, 'bikes/home.html', context)


def cyclist_test(request):
    """
    Simple 8-question quiz -> 5 result types.
    Result leads to catalog for conversions.
    """
    questions = [
        {
            'id': 'surface',
            'title': 'Де ти найчастіше катаєшся?',
            'options': [
                ('asphalt', 'Асфальт / шосе', {'road': 2, 'city': 1}),
                ('gravel', 'Гравій / змішані дороги', {'gravel': 2, 'touring': 1}),
                ('forest', 'Ліс / трейли', {'mtb': 2}),
                ('city', 'Місто / дорога на роботу', {'city': 2}),
            ],
        },
        {
            'id': 'distance',
            'title': 'Яка дистанція тобі найкомфортніша?',
            'options': [
                ('short', '5–15 км', {'city': 2, 'mtb': 1}),
                ('mid', '15–40 км', {'gravel': 2, 'road': 1}),
                ('long', '40–100+ км', {'road': 2, 'touring': 2}),
            ],
        },
        {
            'id': 'speed',
            'title': 'Що важливіше?',
            'options': [
                ('speed', 'Швидкість', {'road': 2}),
                ('comfort', 'Комфорт', {'touring': 2, 'city': 1}),
                ('fun', 'Фан і контроль', {'mtb': 2}),
                ('universal', 'Універсальність', {'gravel': 2}),
            ],
        },
        {
            'id': 'terrain',
            'title': 'Який рельєф ти любиш?',
            'options': [
                ('flat', 'Рівнина', {'road': 2, 'city': 1}),
                ('hills', 'Пагорби', {'gravel': 2, 'road': 1}),
                ('mountains', 'Гори/спуски', {'mtb': 2}),
                ('any', 'Все підряд', {'touring': 2, 'gravel': 1}),
            ],
        },
        {
            'id': 'style',
            'title': 'Як ти катаєшся найчастіше?',
            'options': [
                ('solo', 'Сам/сама', {'road': 1, 'touring': 2}),
                ('group', 'З компанією', {'road': 2, 'gravel': 1}),
                ('adventure', 'Пригоди/нові місця', {'touring': 2, 'gravel': 2}),
                ('park', 'Парки/стежки', {'mtb': 2, 'city': 1}),
            ],
        },
        {
            'id': 'budget',
            'title': 'Бюджет на велосипед?',
            'options': [
                ('low', 'До 20 000 ₴', {'city': 2}),
                ('mid', '20 000 – 60 000 ₴', {'gravel': 2, 'mtb': 1}),
                ('high', '60 000+ ₴', {'road': 2, 'mtb': 2}),
            ],
        },
        {
            'id': 'maintenance',
            'title': 'Ставлення до обслуговування',
            'options': [
                ('simple', 'Хочу мінімум мороки', {'city': 2, 'touring': 1}),
                ('ok', 'Ок, якщо це дає результат', {'road': 2, 'gravel': 1}),
                ('love', 'Люблю техніку і налаштування', {'mtb': 2, 'road': 1}),
            ],
        },
        {
            'id': 'weather',
            'title': 'Коли ти катаєшся?',
            'options': [
                ('summer', 'Переважно в теплу пору', {'road': 2}),
                ('all', 'Цілий рік', {'city': 2, 'touring': 1, 'gravel': 1}),
                ('weekend', 'Вихідні/подорожі', {'touring': 2, 'gravel': 1}),
            ],
        },
    ]

    results = {
        'mtb': {
            'title': 'Ти MTB райдер',
            'desc': 'Тобі важливі контроль, стежки, спуски та пригоди поза асфальтом.',
            'catalog_url': '/catalog/gravel/?q=mtb',
        },
        'road': {
            'title': 'Ти шосейник',
            'desc': 'Ти любиш швидкість, довгі дистанції та рівний асфальт.',
            'catalog_url': '/catalog/road/',
        },
        'city': {
            'title': 'Ти міський велосипедист',
            'desc': 'Тобі потрібен комфортний велосипед для міста, парків та щоденних поїздок.',
            'catalog_url': '/catalog/electric/?q=міський',
        },
        'gravel': {
            'title': 'Ти gravel-райдер',
            'desc': 'Універсальність — твоє все: асфальт, ґрунт, гравій і нові маршрути.',
            'catalog_url': '/catalog/gravel/',
        },
        'touring': {
            'title': 'Ти турист (touring)',
            'desc': 'Тобі важливі комфорт і витривалість для довгих подорожей та нових міст.',
            'catalog_url': '/catalog/gravel/?q=туринг',
        },
    }

    if request.method == 'POST':
        scores = {k: 0 for k in results.keys()}
        missing = []
        for q in questions:
            ans = (request.POST.get(q['id']) or '').strip()
            if not ans:
                missing.append(q['id'])
                continue
            opt = next((o for o in q['options'] if o[0] == ans), None)
            if not opt:
                missing.append(q['id'])
                continue
            weights = opt[2]
            for k, v in weights.items():
                scores[k] = int(scores.get(k, 0)) + int(v)

        if missing:
            messages.error(request, 'Відповідь потрібна на всі питання.')
            return render(request, 'bikes/cyclist_test.html', {'questions': questions, 'results': None})

        # pick best result, stable by predefined order
        order = ['mtb', 'road', 'city', 'gravel', 'touring']
        best = max(order, key=lambda k: scores.get(k, 0))
        return render(
            request,
            'bikes/cyclist_test.html',
            {
                'questions': questions,
                'result': results[best],
                'scores': scores,
            },
        )

    return render(request, 'bikes/cyclist_test.html', {'questions': questions})


def catalog(request, cat_type=None):
    if cat_type in BIKE_TYPE_LEGACY:
        return redirect('catalog_type', cat_type=BIKE_TYPE_LEGACY[cat_type], permanent=True)

    # Default catalog page is "Bikes" (not gear)
    products = Product.objects.select_related('brand', 'category').all()
    bike_categories = (
        Category.objects.filter(category_type='bike')
        .annotate(product_count=Count('products'))
        .annotate(
            _ord=Case(
                When(bike_type='road', then=0),
                When(bike_type='gravel', then=1),
                When(bike_type='kids', then=2),
                When(bike_type='electric', then=3),
                default=99,
                output_field=IntegerField(),
            )
        )
        .order_by('_ord')
    )
    gear_categories = Category.objects.filter(category_type='gear')
    current_category = None
    sidebar_mode = 'bike'  # UI-only: controls which sidebar section is visible

    if cat_type:
        if cat_type in ['road', 'gravel', 'kids', 'electric']:
            current_category = Category.objects.filter(bike_type=cat_type).first()
            products = products.filter(category__bike_type=cat_type)
            sidebar_mode = 'bike'
        elif cat_type in ['helmet', 'clothing', 'glasses', 'shoes', 'gloves', 'lights', 'locks', 'bags', 'tools', 'accessories']:
            current_category = Category.objects.filter(gear_type=cat_type).first()
            products = products.filter(category__gear_type=cat_type)
            sidebar_mode = 'gear'
        elif cat_type == 'gear':
            products = products.filter(category__category_type='gear')
            sidebar_mode = 'gear'
        else:
            current_category = get_object_or_404(Category, slug=cat_type)
            products = products.filter(category=current_category)
    else:
        # If user searches from navbar, we want to search across ALL products,
        # not only the default "bikes" catalog.
        q_peek = request.GET.get('q', '')
        if not q_peek:
            products = products.filter(category__category_type='bike')

    # Filters
    q = request.GET.get('q', '')
    if q:
        # SQLite LIKE/ILIKE has limited Unicode case-folding (UA letters).
        # For the clothing submenu we pass keywords in Cyrillic; use case-sensitive
        # contains against stored lowercase tokens ("чоловіча", "жіноча", "дитяча").
        if cat_type in ['clothing', 'shoes'] and any(
            x in q for x in ['чоловіча', 'жіноча', 'дитяча', 'чоловічі', 'жіночі', 'дитячі']
        ):
            products = products.filter(Q(name__contains=q) | Q(description__contains=q) | Q(brand__name__contains=q))
        else:
            products = products.filter(
                Q(name__icontains=q)
                | Q(description__icontains=q)
                | Q(brand__name__icontains=q)
                | Q(tags__name__icontains=q)
            ).distinct()

    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    if price_min:
        products = products.filter(price__gte=price_min)
    if price_max:
        products = products.filter(price__lte=price_max)

    brand_filter = request.GET.get('brand')
    if brand_filter:
        products = products.filter(brand__slug=brand_filter)

    sort = request.GET.get('sort', 'all')
    sort_map = {
        # Default: highest rating first, then newest
        'all': ('-rating', '-reviews_count', '-created_at'),
        # - "Від дешевих" (price_asc) shows cheap → expensive
        # - "Від дорогих" (price_desc) shows expensive → cheap
        'price_asc': ('price',),
        'price_desc': ('-price',),
        'new': ('-created_at',),
        'name': ('name',),
    }
    if sort == 'new':
        products = products.filter(is_new=True)
    products = products.order_by(*sort_map.get(sort, ('-rating', '-reviews_count', '-created_at')))

    # Price range for filter
    price_range = Product.objects.aggregate(min=Min('price'), max=Max('price'))
    brands_list = Brand.objects.filter(products__in=products).distinct()

    paginator = Paginator(products, 12)
    page = request.GET.get('page', 1)
    products_page = paginator.get_page(page)

    context = {
        'products': products_page,
        'bike_categories': bike_categories,
        'gear_categories': gear_categories,
        'current_category': current_category,
        'cat_type': cat_type,
        'sidebar_mode': sidebar_mode,
        'price_range': price_range,
        'brands_list': brands_list,
        'q': q,
        'sort': sort,
        'selected_price_min': price_min,
        'selected_price_max': price_max,
        'selected_brand': brand_filter,
        'total_count': paginator.count,
    }
    return render(request, 'bikes/catalog.html', context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('brand', 'category').prefetch_related('images'),
        slug=slug,
    )
    related = get_product_suggestions(product, limit=8)
    reviews = product.reviews.all().order_by('-created_at')
    review_form = ReviewForm()

    has_reviewed = False
    if request.user.is_authenticated:
        has_reviewed = product.reviews.filter(author=request.user.username).exists()

    if request.method == 'POST' and request.POST.get('review_submit') == '1':
        if not request.user.is_authenticated:
            messages.info(request, 'Увійдіть або зареєструйтесь, щоб отримати доступ до цієї функції')
            return redirect(f"{reverse('login')}?next={request.get_full_path()}")
            
        if has_reviewed:
            messages.error(request, 'Ви вже залишали відгук на цей товар.')
            return redirect('product_detail', slug=product.slug)
            
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            r = review_form.save(commit=False)
            r.product = product
            r.author = request.user.username  # Force username
            r.is_verified = OrderItem.objects.filter(
                order__user=request.user,
                order__status='paid',
                product=product
            ).exists()
            r.save()
            messages.success(request, 'Дякуємо! Відгук додано.')
            return redirect('product_detail', slug=product.slug)
        messages.error(request, 'Перевірте форму відгуку — є помилки.')

    product_images = [img for img in product.images.all() if img.src]

    suggested_trails, trails_filter_type = get_suggested_trails_for_bike(product, limit=4)

    context = {
        'product': product,
        'product_images': product_images,
        'related': related,
        'reviews': reviews,
        'review_form': review_form,
        'suggested_trails': suggested_trails,
        'trails_filter_type': trails_filter_type,
        'has_reviewed': has_reviewed,
    }
    return render(request, 'bikes/product_detail.html', context)


@login_required_with_message()
@require_POST
def buy_now(request, slug):
    product = get_object_or_404(Product, slug=slug)
    messages.success(request, f'Замовлення на "{product.name}" прийнято. Наш менеджер скоро зв\'яжеться з вами.')
    return redirect('product_detail', slug=product.slug)


@login_required_with_message()
def trails(request):
    all_trails = Trail.objects.all()
    difficulty = request.GET.get('difficulty')
    trail_type = request.GET.get('type')
    city = request.GET.get('city')

    if difficulty:
        all_trails = all_trails.filter(difficulty=difficulty)
    if trail_type:
        all_trails = all_trails.filter(trail_type=trail_type)
    if city:
        all_trails = all_trails.filter(city__icontains=city)

    cities = Trail.objects.values_list('city', flat=True).distinct()

    trail_cards = [{'trail': t} for t in all_trails]

    context = {
        'trails': all_trails,
        'trail_cards': trail_cards,
        'cities': cities,
        'difficulty': difficulty,
        'trail_type': trail_type,
        'selected_city': city,
    }
    return render(request, 'bikes/trails.html', context)


@login_required_with_message()
def trail_detail(request, trail_id: int):
    trail = get_object_or_404(Trail, pk=int(trail_id))
    suggested_bikes = get_suggested_bikes_for_trail(trail, limit=8)
    return render(
        request,
        'bikes/trail_detail.html',
        {
            'trail': trail, 
            'suggested_bikes': suggested_bikes,
            'mapbox_token': getattr(settings, 'MAPBOX_TOKEN', ''),
        },
    )


@login_required_with_message()
def rides_list(request):
    qs = RidePost.objects.select_related('author').filter(is_active=True)

    city = (request.GET.get('city') or '').strip()
    ride_type = (request.GET.get('ride_type') or '').strip()
    level = (request.GET.get('level') or '').strip()

    if city:
        qs = qs.filter(city__icontains=city)
    if ride_type:
        qs = qs.filter(ride_type=ride_type)
    if level:
        qs = qs.filter(level=level)

    posts = list(qs.order_by('-is_featured', 'start_at', '-created_at')[:200])
    return render(
        request,
        'bikes/rides_list.html',
        {
            'posts': posts,
            'city': city,
            'ride_type': ride_type,
            'level': level,
            'ride_type_choices': RidePost.RIDE_TYPE_CHOICES,
            'level_choices': RidePost.LEVEL_CHOICES,
        },
    )


@login_required_with_message()
def ride_new(request):
    ok, msg = can_create_post(request.user)
    if not ok:
        messages.info(request, msg)
        return redirect('premium')

    if request.method == 'POST':
        form = RidePostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.is_featured = bool(is_premium(request.user))
            post.save()
            messages.success(request, 'Пост створено.')
            return redirect('ride_detail', post_id=post.id)
        messages.error(request, 'Перевірте форму — є помилки.')
    else:
        form = RidePostForm()
    return render(request, 'bikes/ride_new.html', {'form': form})


@login_required_with_message()
def ride_detail(request, post_id: int):
    post = get_object_or_404(RidePost.objects.select_related('author'), pk=int(post_id))
    is_author = post.author_id == request.user.id

    my_req = RideRequest.objects.filter(post=post, requester=request.user).first() if not is_author else None
    accepted = bool(my_req and my_req.status == 'accepted')
    can_view_contact = is_author or accepted

    return render(
        request,
        'bikes/ride_detail.html',
        {
            'post': post,
            'is_author': is_author,
            'my_req': my_req,
            'can_view_contact': can_view_contact,
        },
    )


@login_required_with_message()
@require_POST
def ride_request_create(request, post_id: int):
    post = get_object_or_404(RidePost, pk=int(post_id), is_active=True)
    if post.author_id == request.user.id:
        messages.info(request, 'Це ваш пост.')
        return redirect('ride_detail', post_id=post.id)

    ok, msg = can_send_request(request.user)
    if not ok:
        messages.info(request, msg)
        return redirect('premium')

    try:
        RideRequest.objects.create(post=post, requester=request.user, status='pending')
        messages.success(request, 'Заявку надіслано. Очікуйте підтвердження.')
    except Exception:
        # unique_together or other race
        messages.info(request, 'Ви вже надсилали заявку на цей пост.')
    return redirect('ride_detail', post_id=post.id)


@login_required_with_message()
def ride_requests_manage(request, post_id: int):
    post = get_object_or_404(RidePost.objects.select_related('author'), pk=int(post_id))
    if post.author_id != request.user.id:
        messages.error(request, 'Немає доступу.')
        return redirect('ride_detail', post_id=post.id)

    reqs = list(
        RideRequest.objects.filter(post=post)
        .select_related('requester')
        .order_by('-created_at')
    )
    return render(request, 'bikes/ride_requests.html', {'post': post, 'requests': reqs})


@login_required_with_message()
@require_POST
def ride_request_action(request, request_id: int, action: str):
    rr = get_object_or_404(RideRequest.objects.select_related('post'), pk=int(request_id))
    if rr.post.author_id != request.user.id:
        messages.error(request, 'Немає доступу.')
        return redirect('ride_detail', post_id=rr.post_id)

    if action == 'accept':
        rr.status = 'accepted'
        rr.save(update_fields=['status'])
        messages.success(request, 'Заявку прийнято.')
    elif action == 'decline':
        rr.status = 'declined'
        rr.save(update_fields=['status'])
        messages.info(request, 'Заявку відхилено.')
    else:
        messages.error(request, 'Невідома дія.')
    return redirect('ride_requests', post_id=rr.post_id)


def stores(request):
    all_stores = Store.objects.all()
    locations = StoreLocation.objects.select_related('store').all()
    store_points = []
    for loc in locations:
        if loc.latitude is None or loc.longitude is None:
            continue
        store_points.append(
            {
                'store': loc.store.name,
                'title': loc.title or loc.store.name,
                'city': loc.city,
                'address': loc.address,
                'phone': loc.store.phone or '',
                'lat': float(loc.latitude),
                'lng': float(loc.longitude),
            }
        )
    context = {
        'stores': all_stores,
        'store_locations': locations,
        'store_points': store_points,
        'mapbox_token': getattr(settings, 'MAPBOX_TOKEN', ''),
    }
    return render(request, 'bikes/stores.html', context)


@login_required_with_message()
def compare_prices(request):
    product_ids = [pid for pid in request.GET.getlist('products') if str(pid).isdigit()]
    if not product_ids:
        return render(request, 'bikes/compare.html', {'products': []})
    id_order = {int(p): i for i, p in enumerate(product_ids)}
    qs = (
        Product.objects.filter(pk__in=product_ids)
        .select_related('brand', 'category')
        .prefetch_related('store_prices__store', 'images')
    )
    products = list(qs)
    products.sort(key=lambda p: id_order.get(p.id, 999))
    pids = [p.id for p in products]
    for p in products:
        other_ids = [str(x) for x in pids if x != p.id]
        p.compare_remove_url = (
            '/compare/?' + '&'.join(f'products={x}' for x in other_ids) if other_ids else '/compare/'
        )
    return render(request, 'bikes/compare.html', {'products': products})


@login_required_with_message()
def cart_view(request):
    lines = cart_lines(request.session)
    total = cart_total(request.session)
    return render(request, 'bikes/cart.html', {'lines': lines, 'total': total})


@login_required_with_message()
def cart_modal_fragment(request):
    lines = cart_lines(request.session)
    total = cart_total(request.session)
    html = render_to_string('bikes/partials/cart_modal.html', {'lines': lines, 'total': total}, request=request)
    return JsonResponse({'html': html, 'cart_count': sum(l.qty for l in lines), 'total': total})


@login_required_with_message()
def checkout_view(request):
    lines = cart_lines(request.session)
    total = cart_total(request.session)
    profile = getattr(request.user, 'profile', None)
    return render(request, 'bikes/checkout.html', {'lines': lines, 'total': total, 'profile': profile})


@login_required_with_message()
@require_POST
def create_payment_session(request):
    lines = cart_lines(request.session)
    if not lines:
        messages.info(request, 'Кошик порожній.')
        return redirect('cart')

    if not getattr(settings, 'STRIPE_SECRET_KEY', ''):
        messages.error(request, 'Оплата тимчасово недоступна: не налаштований STRIPE_SECRET_KEY.')
        return redirect('checkout')

    # Collect recipient fields (simple checkout)
    recipient_name = (request.POST.get('recipient_name') or '').strip()
    recipient_phone = (request.POST.get('recipient_phone') or '').strip()
    recipient_city = (request.POST.get('recipient_city') or '').strip()
    recipient_email = (request.POST.get('recipient_email') or '').strip()
    comment = (request.POST.get('comment') or '').strip()

    # Validate basic formats (server-side)
    # - name/city: letters + spaces + hyphen + apostrophe
    # - phone: digits with optional +, spaces, (), -
    name_re = re.compile(r"^[A-Za-zА-Яа-яІіЇїЄєҐґ'\-\s]{2,200}$")
    city_re = re.compile(r"^[A-Za-zА-Яа-яІіЇїЄєҐґ'\-\s]{2,120}$")
    phone_re = re.compile(r"^[0-9+\-\s()]{7,30}$")
    digits_count = sum(ch.isdigit() for ch in recipient_phone)

    errors = []
    if not recipient_name or not name_re.match(recipient_name):
        errors.append("ПІБ має містити тільки літери (без цифр).")
    if not recipient_city or not city_re.match(recipient_city):
        errors.append("Місто має містити тільки літери (без цифр).")
    if not recipient_phone or not phone_re.match(recipient_phone) or digits_count < 7:
        errors.append("Телефон має містити тільки цифри (можна +, пробіли, дужки, дефіси).")
    if not recipient_email:
        errors.append("Email обовʼязковий.")

    if errors:
        for e in errors[:3]:
            messages.error(request, e)
        profile = getattr(request.user, 'profile', None)
        total = cart_total(request.session)
        return render(
            request,
            'bikes/checkout.html',
            {
                'lines': lines,
                'total': total,
                'profile': profile,
                'form_data': {
                    'recipient_name': recipient_name,
                    'recipient_phone': recipient_phone,
                    'recipient_city': recipient_city,
                    'recipient_email': recipient_email,
                    'comment': comment,
                },
            },
        )

    # Create local order first
    order = Order.objects.create(
        user=request.user,
        status='pending',
        currency='UAH',
        recipient_name=recipient_name,
        recipient_phone=recipient_phone,
        recipient_city=recipient_city,
        recipient_email=recipient_email,
        comment=comment,
    )

    total_amount = 0
    for line in lines:
        unit_price = line.product.price
        OrderItem.objects.create(
            order=order,
            product=line.product,
            product_name=line.product.name,
            qty=int(line.qty),
            unit_price=unit_price,
        )
        total_amount += float(unit_price) * int(line.qty)
    order.total_amount = total_amount
    order.save(update_fields=['total_amount'])

    # Stripe Checkout Session
    import stripe

    stripe.api_key = settings.STRIPE_SECRET_KEY

    success_url = request.build_absolute_uri(reverse('payment_success')) + '?session_id={CHECKOUT_SESSION_ID}'
    cancel_url = request.build_absolute_uri(reverse('payment_cancel')) + f'?order={order.pk}'

    stripe_line_items = []
    for line in lines:
        stripe_line_items.append(
            {
                'price_data': {
                    'currency': 'uah',
                    'product_data': {'name': line.product.name},
                    'unit_amount': int(float(line.product.price) * 100),
                },
                'quantity': int(line.qty),
            }
        )

    try:
        session = stripe.checkout.Session.create(
            mode='payment',
            line_items=stripe_line_items,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={'order_id': str(order.pk), 'user_id': str(request.user.pk)},
        )
    except Exception as e:
        order.delete()
        messages.error(request, f'Помилка Stripe: {e}')
        return redirect('checkout')

    order.stripe_session_id = session.id
    order.save(update_fields=['stripe_session_id'])
    return redirect(session.url, permanent=False)


@login_required_with_message()
def payment_success(request):
    session_id = (request.GET.get('session_id') or '').strip()
    if not session_id:
        messages.error(request, 'Не вдалося підтвердити оплату (немає session_id).')
        return redirect('checkout')

    if not getattr(settings, 'STRIPE_SECRET_KEY', ''):
        messages.error(request, 'Оплата тимчасово недоступна: не налаштований STRIPE_SECRET_KEY.')
        return redirect('checkout')

    import stripe

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception:
        order = Order.objects.filter(stripe_session_id=session_id, user=request.user).first()
        if order:
            return render(request, 'bikes/payment_success.html', {'order': order})
        messages.error(request, 'Не вдалося підтвердити оплату через Stripe.')
        return redirect('checkout')

    order_id = (session.metadata or {}).get('order_id')
    order = Order.objects.filter(pk=order_id, user=request.user).first() if order_id else None
    if not order:
        order = Order.objects.filter(stripe_session_id=session_id, user=request.user).first()

    if not order:
        messages.error(request, 'Замовлення не знайдено.')
        return redirect('checkout')

    # Mark paid
    try:
        payment_status = getattr(session, 'payment_status', None) or session.get('payment_status')
        payment_intent = getattr(session, 'payment_intent', None) or session.get('payment_intent') or ''
    except Exception:
        payment_status = None
        payment_intent = ''

    if payment_status == 'paid' and order.status != 'paid':
        order.status = 'paid'
        order.paid_at = timezone.now()
        order.stripe_payment_intent_id = payment_intent or ''
        order.save(update_fields=['status', 'paid_at', 'stripe_payment_intent_id'])

        # Clear cart after successful payment
        request.session.pop('velo_cart_v1', None)
        request.session.modified = True

    return render(request, 'bikes/payment_success.html', {'order': order})


@login_required_with_message()
def payment_cancel(request):
    order_id = (request.GET.get('order') or '').strip()
    order = None
    if order_id.isdigit():
        order = Order.objects.filter(pk=int(order_id), user=request.user).first()
        if order and order.status == 'pending':
            order.status = 'cancelled'
            order.save(update_fields=['status'])
    return render(request, 'bikes/payment_cancel.html', {'order': order})


@login_required_with_message()
def premium_page(request):
    sub = UserSubscription.objects.filter(user=request.user).first()
    return render(request, 'bikes/premium.html', {'sub': sub})


@login_required_with_message()
@require_POST
def premium_checkout(request):
    if not getattr(settings, 'STRIPE_SECRET_KEY', ''):
        messages.error(request, 'Premium тимчасово недоступний: не налаштований STRIPE_SECRET_KEY.')
        return redirect('premium')
    if not getattr(settings, 'STRIPE_PREMIUM_PRICE_ID', ''):
        messages.error(request, 'Premium тимчасово недоступний: не налаштований STRIPE_PREMIUM_PRICE_ID.')
        return redirect('premium')

    import stripe

    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Ensure local subscription row exists
    UserSubscription.objects.get_or_create(user=request.user, defaults={'tier': 'free'})

    success_url = request.build_absolute_uri(reverse('premium_success')) + '?session_id={CHECKOUT_SESSION_ID}'
    cancel_url = request.build_absolute_uri(reverse('premium_cancel'))

    session = stripe.checkout.Session.create(
        mode='subscription',
        line_items=[{'price': settings.STRIPE_PREMIUM_PRICE_ID, 'quantity': 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(request.user.pk),
        metadata={'user_id': str(request.user.pk)},
    )
    return redirect(session.url, permanent=False)


@login_required_with_message()
def premium_success(request):
    session_id = (request.GET.get('session_id') or '').strip()
    if not session_id:
        messages.error(request, 'Не вдалося підтвердити Premium (немає session_id).')
        return redirect('premium')

    if not getattr(settings, 'STRIPE_SECRET_KEY', ''):
        messages.error(request, 'Premium тимчасово недоступний: не налаштований STRIPE_SECRET_KEY.')
        return redirect('premium')

    import stripe

    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.retrieve(session_id, expand=['subscription', 'customer'])
    subscription = session.get('subscription')
    customer = session.get('customer')

    sub, _ = UserSubscription.objects.get_or_create(user=request.user)
    sub.tier = 'premium'
    sub.status = 'active'
    sub.stripe_customer_id = customer.get('id') if isinstance(customer, dict) else (customer or '')
    sub.stripe_subscription_id = subscription.get('id') if isinstance(subscription, dict) else (subscription or '')

    # current_period_end is a unix timestamp on subscription
    period_end = None
    if isinstance(subscription, dict):
        ts = subscription.get('current_period_end')
        if ts:
            period_end = timezone.datetime.fromtimestamp(int(ts), tz=timezone.get_current_timezone())
    sub.current_period_end = period_end
    sub.save()

    return render(request, 'bikes/premium_success.html', {'sub': sub})


@login_required_with_message()
def premium_cancel(request):
    return render(request, 'bikes/premium_cancel.html')


@login_required_with_message()
@require_POST
def cart_add(request, product_id: int):
    qty = request.POST.get('qty', '1')
    add_to_cart(request.session, int(product_id), int(qty or 1))
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        lines = cart_lines(request.session)
        total = cart_total(request.session)
        html = render_to_string('bikes/partials/cart_modal.html', {'lines': lines, 'total': total}, request=request)
        return JsonResponse({'ok': True, 'html': html, 'cart_count': sum(l.qty for l in lines), 'total': total})
    messages.success(request, 'Додано в кошик.')
    nxt = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('cart')
    return redirect(nxt)


@login_required_with_message()
@require_POST
def cart_update(request, product_id: int):
    qty = request.POST.get('qty', '1')
    set_qty(request.session, int(product_id), int(qty or 1))
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        lines = cart_lines(request.session)
        total = cart_total(request.session)
        html = render_to_string('bikes/partials/cart_modal.html', {'lines': lines, 'total': total}, request=request)
        return JsonResponse({'ok': True, 'html': html, 'cart_count': sum(l.qty for l in lines), 'total': total})
    messages.success(request, 'Кошик оновлено.')
    return redirect('cart')


@login_required_with_message()
@require_POST
def cart_remove(request, product_id: int):
    remove_from_cart(request.session, int(product_id))
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        lines = cart_lines(request.session)
        total = cart_total(request.session)
        html = render_to_string('bikes/partials/cart_modal.html', {'lines': lines, 'total': total}, request=request)
        return JsonResponse({'ok': True, 'html': html, 'cart_count': sum(l.qty for l in lines), 'total': total})
    messages.info(request, 'Товар прибрано з кошика.')
    return redirect('cart')

def _safe_redirect_url(request, url):
    if not url:
        return None
    if url_has_allowed_host_and_scheme(
        url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return url
    return None


def register_view(request):
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Акаунт створено успішно.')
            nxt = _safe_redirect_url(request, request.POST.get('next') or request.GET.get('next'))
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'ok': True, 'redirect': (nxt or reverse('profile'))})
            return redirect(nxt or 'profile')
    else:
        form = RegisterForm()

    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # invalid form → return errors for modal
        errs = []
        for field, field_errors in form.errors.items():
            for e in field_errors:
                errs.append(str(e))
        non_field = [str(e) for e in form.non_field_errors()]
        return JsonResponse({'ok': False, 'errors': non_field + errs}, status=400)

    return render(request, 'bikes/auth_register.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


def login_view(request):
    if request.user.is_authenticated:
        nxt = _safe_redirect_url(request, request.GET.get('next'))
        return redirect(nxt or 'profile')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, 'Вхід виконано.')
            nxt = _safe_redirect_url(request, request.POST.get('next') or request.GET.get('next'))
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'ok': True, 'redirect': (nxt or reverse('profile'))})
            return redirect(nxt or 'profile')
    else:
        form = LoginForm()

    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        errs = []
        for field, field_errors in form.errors.items():
            for e in field_errors:
                errs.append(str(e))
        non_field = [str(e) for e in form.non_field_errors()]
        return JsonResponse({'ok': False, 'errors': non_field + errs}, status=400)

    return render(request, 'bikes/auth_login.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Ви вийшли з акаунту.')
    return redirect('home')


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Профіль збережено.')
            return redirect('profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)

    ai_records = list(
        AIChatRecord.objects.filter(user=request.user).order_by('-created_at')[:25]
    )
    orders = (
        Order.objects.filter(user=request.user, status='paid')
        .prefetch_related('items')
        .order_by('-created_at')[:20]
    )

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
        'ai_records': ai_records,
        'orders': orders,
    }
    return render(request, 'bikes/profile.html', context)
