from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(blank=True, unique=True)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='brands/')),
                ('country', models.CharField(blank=True, max_length=100)),
                ('description', models.TextField(blank=True)),
                ('website', models.URLField(blank=True)),
            ],
            options={
                'verbose_name': 'Бренд',
                'verbose_name_plural': 'Бренди',
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Назва')),
                ('slug', models.SlugField(blank=True, unique=True)),
                ('category_type', models.CharField(choices=[('bike', 'Велосипед'), ('gear', 'Екіпірування')], default='bike', max_length=20)),
                ('bike_type', models.CharField(blank=True, choices=[('mens', 'Чоловічі'), ('womens', 'Жіночі'), ('kids', 'Дитячі'), ('electric', 'Електровелосипеди')], max_length=20, null=True)),
                ('gear_type', models.CharField(blank=True, choices=[('helmet', 'Шоломи'), ('clothing', 'Вело-форма'), ('glasses', 'Окуляри'), ('shoes', 'Вело-туфлі'), ('gloves', 'Рукавички'), ('lights', 'Ліхтарі'), ('locks', 'Замки'), ('bags', 'Сумки'), ('tools', 'Інструменти'), ('accessories', 'Аксесуари')], max_length=20, null=True)),
                ('description', models.TextField(blank=True)),
                ('icon', models.CharField(default='🚲', max_length=50)),
            ],
            options={
                'verbose_name': 'Категорія',
                'verbose_name_plural': 'Категорії',
            },
        ),
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('website', models.URLField()),
                ('logo_url', models.URLField(blank=True)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('phone', models.CharField(blank=True, max_length=50)),
                ('address', models.CharField(blank=True, max_length=300)),
                ('is_online', models.BooleanField(default=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Магазин',
                'verbose_name_plural': 'Магазини',
            },
        ),
        migrations.CreateModel(
            name='Trail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('city', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('difficulty', models.CharField(choices=[('easy', 'Легка'), ('medium', 'Середня'), ('hard', 'Важка'), ('extreme', 'Екстремальна')], max_length=20)),
                ('trail_type', models.CharField(choices=[('road', 'Шосе'), ('mtb', 'Гірська'), ('city', 'Міська'), ('mixed', 'Змішана')], max_length=20)),
                ('distance_km', models.FloatField()),
                ('elevation_m', models.IntegerField(default=0)),
                ('duration_hours', models.FloatField()),
                ('image_url', models.URLField(blank=True)),
                ('map_url', models.URLField(blank=True)),
                ('rating', models.FloatField(default=0.0)),
            ],
            options={
                'verbose_name': 'Траса',
                'verbose_name_plural': 'Траси',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Назва')),
                ('slug', models.SlugField(blank=True, unique=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Ціна (₴)')),
                ('old_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Стара ціна')),
                ('description', models.TextField(verbose_name='Опис')),
                ('short_description', models.CharField(blank=True, max_length=300)),
                ('image', models.ImageField(blank=True, null=True, upload_to='products/', verbose_name='Фото')),
                ('image_url', models.URLField(blank=True, verbose_name='URL фото')),
                ('condition', models.CharField(choices=[('new', 'Новий'), ('used', 'Вживаний'), ('refurbished', 'Відновлений')], default='new', max_length=20)),
                ('in_stock', models.BooleanField(default=True, verbose_name='В наявності')),
                ('is_featured', models.BooleanField(default=False, verbose_name='Рекомендований')),
                ('is_new', models.BooleanField(default=False, verbose_name='Новинка')),
                ('rating', models.FloatField(default=0.0)),
                ('reviews_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('wheel_size', models.CharField(blank=True, max_length=20, verbose_name='Розмір колеса')),
                ('frame_size', models.CharField(blank=True, max_length=50, verbose_name='Розмір рами')),
                ('frame_material', models.CharField(blank=True, max_length=100, verbose_name='Матеріал рами')),
                ('speeds', models.IntegerField(blank=True, null=True, verbose_name='Кількість швидкостей')),
                ('weight', models.FloatField(blank=True, null=True, verbose_name='Вага (кг)')),
                ('color', models.CharField(blank=True, max_length=50, verbose_name='Колір')),
                ('age_min', models.IntegerField(blank=True, null=True, verbose_name='Вік від')),
                ('age_max', models.IntegerField(blank=True, null=True, verbose_name='Вік до')),
                ('battery_capacity', models.CharField(blank=True, max_length=50, verbose_name='Ємність батареї')),
                ('motor_power', models.CharField(blank=True, max_length=50, verbose_name='Потужність мотора')),
                ('range_km', models.IntegerField(blank=True, null=True, verbose_name='Запас ходу (км)')),
                ('brand', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='bikes.brand')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='bikes.category')),
            ],
            options={
                'verbose_name': 'Продукт',
                'verbose_name_plural': 'Продукти',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ProductStore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('url', models.URLField(blank=True)),
                ('in_stock', models.BooleanField(default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='store_prices', to='bikes.product')),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bikes.store')),
            ],
            options={
                'verbose_name': 'Ціна в магазині',
                'verbose_name_plural': 'Ціни в магазинах',
                'ordering': ['price'],
            },
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author', models.CharField(max_length=100)),
                ('rating', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])),
                ('text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='bikes.product')),
            ],
            options={
                'verbose_name': 'Відгук',
                'verbose_name_plural': 'Відгуки',
            },
        ),
    ]
