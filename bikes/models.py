from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
import uuid
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from taggit.managers import TaggableManager


class Category(models.Model):
    BIKE_TYPES = [
        ('road', 'Шосейні'),
        ('gravel', 'Гравійні'),
        ('kids', 'Дитячі'),
        ('electric', 'Електровелосипеди'),
    ]
    GEAR_TYPES = [
        ('helmet', 'Шоломи'),
        ('clothing', 'Вело-форма'),
        ('glasses', 'Окуляри'),
        ('shoes', 'Вело-туфлі'),
        ('gloves', 'Рукавички'),
        ('lights', 'Ліхтарі'),
        ('locks', 'Замки'),
        ('bags', 'Сумки'),
        ('tools', 'Інструменти'),
        ('accessories', 'Аксесуари'),
    ]

    name = models.CharField(max_length=100, verbose_name='Назва')
    slug = models.SlugField(unique=True, blank=True)
    category_type = models.CharField(max_length=20, choices=[('bike', 'Велосипед'), ('gear', 'Екіпірування')], default='bike')
    bike_type = models.CharField(max_length=20, choices=BIKE_TYPES, blank=True, null=True)
    gear_type = models.CharField(max_length=20, choices=GEAR_TYPES, blank=True, null=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='🚲')

    class Meta:
        verbose_name = 'Категорія'
        verbose_name_plural = 'Категорії'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    country = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)

    class Meta:
        verbose_name = 'Бренд'
        verbose_name_plural = 'Бренди'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    CONDITION_CHOICES = [
        ('new', 'Новий'),
        ('used', 'Вживаний'),
        ('refurbished', 'Відновлений'),
    ]

    name = models.CharField(max_length=200, verbose_name='Назва')
    slug = models.SlugField(unique=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Ціна (₴)')
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Стара ціна')
    description = models.TextField(verbose_name='Опис')
    short_description = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Фото')
    image_url = models.URLField(blank=True, verbose_name='URL фото')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='new')
    in_stock = models.BooleanField(default=True, verbose_name='В наявності')
    is_featured = models.BooleanField(default=False, verbose_name='Рекомендований')
    is_new = models.BooleanField(default=False, verbose_name='Новинка')
    rating = models.FloatField(default=0.0)
    reviews_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Bike-specific fields
    wheel_size = models.CharField(max_length=20, blank=True, verbose_name='Розмір колеса')
    frame_size = models.CharField(max_length=50, blank=True, verbose_name='Розмір рами')
    frame_material = models.CharField(max_length=100, blank=True, verbose_name='Матеріал рами')
    speeds = models.IntegerField(null=True, blank=True, verbose_name='Кількість швидкостей')
    weight = models.FloatField(null=True, blank=True, verbose_name='Вага (кг)')
    color = models.CharField(max_length=50, blank=True, verbose_name='Колір')
    age_min = models.IntegerField(null=True, blank=True, verbose_name='Вік від')
    age_max = models.IntegerField(null=True, blank=True, verbose_name='Вік до')

    # Electric bike fields
    battery_capacity = models.CharField(max_length=50, blank=True, verbose_name='Ємність батареї')
    motor_power = models.CharField(max_length=50, blank=True, verbose_name='Потужність мотора')
    range_km = models.IntegerField(null=True, blank=True, verbose_name='Запас ходу (км)')

    # Gear sizing (shoes/clothing/helmets/gloves etc.)
    available_sizes = models.CharField(
        max_length=220,
        blank=True,
        verbose_name='Доступні розміри',
        help_text='Напр.: 38,39,40,41 або S,M,L',
    )

    bag_features = models.TextField(
        blank=True,
        verbose_name='Сумки: особливості',
        help_text='Один пункт на рядок — список у блоці опису',
    )
    bag_volume = models.CharField(max_length=80, blank=True, verbose_name='Сумки: обсяг')
    bag_weight_note = models.CharField(max_length=80, blank=True, verbose_name='Сумки: вага (текст)')
    bag_dimensions = models.TextField(blank=True, verbose_name='Сумки: розміри')

    tags = TaggableManager(blank=True, verbose_name='Теги')

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукти'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or str(uuid.uuid4())[:8]
            slug = base
            n = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return int((1 - self.price / self.old_price) * 100)
        return 0

    @property
    def bag_feature_lines(self):
        if not self.bag_features:
            return []
        return [ln.strip() for ln in self.bag_features.splitlines() if ln.strip()]

    @property
    def bag_dimension_lines(self):
        if not self.bag_dimensions:
            return []
        return [ln.strip() for ln in self.bag_dimensions.splitlines() if ln.strip()]

    @property
    def key_feature_lines(self):
        """
        Short bullet list for product pages (max ~6).
        Priority:
        - bags: bag_features lines
        - description: lines starting with '-', '•', '*'
        - fallback: a few structured fields
        """
        lines = []
        if self.bag_feature_lines:
            lines = list(self.bag_feature_lines)
        else:
            raw = (self.description or '').splitlines()
            for ln in raw:
                s = ln.strip()
                if not s:
                    continue
                if s.startswith(('-', '•', '*')):
                    s = s.lstrip('-•*').strip()
                    if s:
                        lines.append(s)
                if len(lines) >= 6:
                    break

        if not lines:
            if self.category and self.category.category_type == 'bike':
                if self.frame_material:
                    lines.append(f'Матеріал рами: {self.frame_material}')
                if self.speeds:
                    lines.append(f'Трансмісія: {self.speeds} швидкостей')
                if self.wheel_size:
                    lines.append(f'Колеса: {self.wheel_size}"')
                if self.weight:
                    lines.append(f'Вага: {self.weight} кг')
                if self.range_km:
                    lines.append(f'Запас ходу: до {self.range_km} км')
            else:
                if self.short_description:
                    lines.append(self.short_description)
                if self.color:
                    lines.append(f'Колір: {self.color}')
                if self.available_sizes:
                    lines.append(f'Розміри: {self.available_sizes}')

        out = []
        for x in lines:
            x = (x or '').strip()
            if x and x not in out:
                out.append(x)
            if len(out) >= 6:
                break
        return out

    @property
    def image_src(self):
        if self.image:
            url = self.image.url
            if url.startswith('http'):
                return url
            if self.image_url:
                return self.image_url
            return url
        return self.image_url or ''

    @property
    def primary_image_src(self):
        """
        Best-effort image for UI (catalog/cart/checkout):
        - main Product.image / image_url
        - first gallery image (ProductImage) if present
        """
        src = self.image_src
        if src:
            return src
        try:
            first = self.images.first()
            if first and first.src:
                return first.src
        except Exception:
            pass
        return ''


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Фото')
    image_url = models.URLField(blank=True, verbose_name='URL фото')
    alt = models.CharField(max_length=200, blank=True, verbose_name='Alt текст')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Фото товару'
        verbose_name_plural = 'Фото товарів'
        ordering = ['sort_order', 'id']

    def __str__(self):
        label = self.alt.strip() if self.alt else ''
        return label or f"Фото #{self.pk} для {self.product}"

    @property
    def src(self):
        if self.image:
            return self.image.url
        return self.image_url or ''


@receiver(post_save, sender=Product)
def _ensure_primary_product_image(sender, instance, created, **kwargs):
    primary = instance.images.order_by('sort_order', 'id').first()

    if instance.image:
        if primary:
            if primary.image != instance.image:
                ProductImage.objects.filter(pk=primary.pk).update(
                    image=instance.image, image_url=''
                )
        else:
            ProductImage.objects.create(
                product=instance, image=instance.image,
                alt=instance.name or '', sort_order=0,
            )
        return

    if instance.image_url:
        if primary and not primary.image:
            if primary.image_url != instance.image_url:
                ProductImage.objects.filter(pk=primary.pk).update(
                    image_url=instance.image_url
                )
        elif not primary:
            ProductImage.objects.create(
                product=instance, image_url=instance.image_url,
                alt=instance.name or '', sort_order=0,
            )


class Store(models.Model):
    name = models.CharField(max_length=200)
    website = models.URLField()
    logo_url = models.URLField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=300, blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    is_online = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазини'

    def __str__(self):
        return self.name


class StoreLocation(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='locations')
    title = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=300, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        verbose_name = 'Точка магазину'
        verbose_name_plural = 'Точки магазинів'

    def __str__(self):
        base = self.title or self.store.name
        loc = ', '.join([p for p in [self.city, self.address] if p])
        return f"{base} ({loc})" if loc else base


class ProductStore(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='store_prices')
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    url = models.URLField(blank=True)
    in_stock = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ціна в магазині'
        verbose_name_plural = 'Ціни в магазинах'
        ordering = ['price']

    def __str__(self):
        return f"{self.product.name} — {self.store.name}: {self.price}₴"


class Trail(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Легка'),
        ('medium', 'Середня'),
        ('hard', 'Важка'),
        ('extreme', 'Екстремальна'),
    ]
    TRAIL_TYPE = [
        ('road', 'Шосе'),
        ('mtb', 'Гірська'),
        ('city', 'Міська'),
        ('mixed', 'Змішана'),
    ]

    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    description = models.TextField()
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    trail_type = models.CharField(max_length=20, choices=TRAIL_TYPE)
    distance_km = models.FloatField()
    elevation_m = models.IntegerField(default=0)
    duration_hours = models.FloatField()
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    image_url = models.CharField(max_length=500, blank=True)
    map_url = models.URLField(blank=True)
    rating = models.FloatField(default=0.0)

    class Meta:
        verbose_name = 'Траса'
        verbose_name_plural = 'Траси'

    def __str__(self):
        return f"{self.name} ({self.city})"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    author = models.CharField(max_length=100)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    text = models.TextField()
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Відгук'
        verbose_name_plural = 'Відгуки'

    def __str__(self):
        return f"{self.author} — {self.product.name}"


@receiver(post_save, sender=Review)
def _review_saved_refresh_rating(sender, instance, **kwargs):
    from bikes.services import recompute_product_rating

    recompute_product_rating(instance.product)


@receiver(post_delete, sender=Review)
def _review_deleted_refresh_rating(sender, instance, **kwargs):
    from bikes.services import recompute_product_rating

    product = Product.objects.filter(pk=instance.product_id).first()
    if product:
        recompute_product_rating(product)


class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('female', 'Жіноча'),
        ('male', 'Чоловіча'),
        ('other', 'Інше'),
        ('na', 'Не вказувати'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True, verbose_name='Фото профілю')
    phone = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    weight_kg = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Вага (кг)')
    height_cm = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Ріст (см)')
    age = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Вік')
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        default='na',
        blank=True,
        verbose_name='Стать',
    )

    class Meta:
        verbose_name = 'Профіль користувача'
        verbose_name_plural = 'Профілі користувачів'

    def __str__(self):
        return self.user.username


class Order(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Чернетка'),
        ('pending', 'Очікує оплату'),
        ('paid', 'Оплачено'),
        ('cancelled', 'Скасовано'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='UAH')

    recipient_name = models.CharField(max_length=200, blank=True)
    recipient_phone = models.CharField(max_length=50, blank=True)
    recipient_city = models.CharField(max_length=100, blank=True)
    recipient_email = models.EmailField(blank=True)
    comment = models.TextField(blank=True)

    stripe_session_id = models.CharField(max_length=255, blank=True, db_index=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.pk} — {self.user.username} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    product_name = models.CharField(max_length=300)
    qty = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Позиція замовлення'
        verbose_name_plural = 'Позиції замовлення'

    def __str__(self):
        return f"{self.product_name} × {self.qty}"


class RidePost(models.Model):
    RIDE_TYPE_CHOICES = [
        ('road', 'Шосе'),
        ('mtb', 'MTB'),
        ('city', 'Місто'),
        ('mixed', 'Змішано'),
    ]
    LEVEL_CHOICES = [
        ('easy', 'Легко'),
        ('medium', 'Середньо'),
        ('fast', 'Швидко'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ride_posts')
    city = models.CharField(max_length=120)
    start_at = models.DateTimeField()
    distance_km = models.FloatField(blank=True, null=True)
    pace = models.CharField(max_length=80, blank=True)
    ride_type = models.CharField(max_length=20, choices=RIDE_TYPE_CHOICES, default='mixed')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='medium')
    note = models.TextField(blank=True)
    contact_handle = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Пошук напарника'
        verbose_name_plural = 'Пошук напарника'
        ordering = ['-is_featured', '-start_at', '-created_at']

    def __str__(self):
        return f"{self.city} — {self.get_ride_type_display()} ({self.author.username})"


class RideRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Очікує'),
        ('accepted', 'Прийнято'),
        ('declined', 'Відхилено'),
        ('cancelled', 'Скасовано'),
    ]

    post = models.ForeignKey(RidePost, on_delete=models.CASCADE, related_name='requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ride_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Заявка на катання'
        verbose_name_plural = 'Заявки на катання'
        unique_together = (('post', 'requester'),)
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.requester.username} → {self.post_id} ({self.status})"


class UserSubscription(models.Model):
    TIER_CHOICES = [
        ('free', 'Free'),
        ('premium', 'Premium'),
    ]
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('past_due', 'Проблема з оплатою'),
        ('canceled', 'Скасована'),
        ('incomplete', 'Не завершено'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='free')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, db_index=True)
    current_period_end = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Підписка'
        verbose_name_plural = 'Підписки'

    def __str__(self):
        return f"{self.user.username}: {self.tier} ({self.status})"
