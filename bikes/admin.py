from django.contrib import admin
from .models import (
    Category,
    Brand,
    Product,
    ProductImage,
    Store,
    StoreLocation,
    ProductStore,
    Trail,
    Review,
    UserProfile,
    Order,
    OrderItem,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'bike_type', 'gear_type']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'website']
    prepopulated_fields = {'slug': ('name',)}


class ProductStoreInline(admin.TabularInline):
    model = ProductStore
    extra = 2


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 1


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ('sort_order', 'image', 'image_url', 'alt')
    ordering = ('sort_order', 'id')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'category', 'price', 'in_stock', 'is_featured']
    list_filter = ['category', 'brand', 'in_stock', 'is_featured', 'is_new']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductStoreInline, ReviewInline]
    fieldsets = (
        ('Основне', {'fields': ('name', 'slug', 'brand', 'category', 'short_description', 'description', 'image', 'image_url')}),
        ('Ціни', {'fields': ('price', 'old_price', 'condition', 'in_stock')}),
        ('Розміри (екіпірування)', {'fields': ('available_sizes',), 'classes': ('collapse',)}),
        ('Вело-сумки (детальний опис на сайті)', {'fields': ('bag_features', 'bag_volume', 'bag_weight_note', 'bag_dimensions'), 'classes': ('collapse',)}),
        ('Характеристики велосипеда', {'fields': ('wheel_size', 'frame_size', 'frame_material', 'speeds', 'weight', 'color', 'age_min', 'age_max'), 'classes': ('collapse',)}),
        ('Електровелосипед', {'fields': ('battery_capacity', 'motor_power', 'range_km'), 'classes': ('collapse',)}),
        ('Додатково', {'fields': ('is_featured', 'is_new', 'rating', 'reviews_count')}),
    )


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'is_online', 'phone', 'website']
    search_fields = ['name', 'city', 'address']
    fields = (
        'name', 'website', 'logo_url', 'city', 'phone', 'address',
        'latitude', 'longitude', 'is_online', 'description',
    )

@admin.register(StoreLocation)
class StoreLocationAdmin(admin.ModelAdmin):
    list_display = ['store', 'title', 'city', 'address', 'latitude', 'longitude']
    list_filter = ['city', 'store']
    search_fields = ['store__name', 'title', 'city', 'address']
    fields = ('store', 'title', 'city', 'address', 'latitude', 'longitude')


@admin.register(Trail)
class TrailAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'difficulty', 'distance_km', 'trail_type', 'latitude', 'longitude']
    list_filter = ['difficulty', 'trail_type', 'city']
    search_fields = ['name', 'city', 'description']
    fields = (
        'name',
        'city',
        'description',
        'difficulty',
        'trail_type',
        'distance_km',
        'duration_hours',
        'elevation_m',
        'latitude',
        'longitude',
        'image_url',
        'map_url',
        'rating',
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['author', 'product', 'rating', 'created_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'city', 'gender', 'age', 'height_cm', 'weight_kg']
    search_fields = ['user__username', 'user__email', 'phone', 'city']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'qty', 'unit_price')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total_amount', 'currency', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['id', 'user__username', 'recipient_name', 'recipient_phone', 'stripe_session_id']
    readonly_fields = ('created_at', 'paid_at', 'stripe_session_id', 'stripe_payment_intent_id')
    inlines = [OrderItemInline]



