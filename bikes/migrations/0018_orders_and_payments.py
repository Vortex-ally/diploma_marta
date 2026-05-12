from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('bikes', '0017_alter_trail_image_url'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('draft', 'Чернетка'), ('pending', 'Очікує оплату'), ('paid', 'Оплачено'), ('cancelled', 'Скасовано')], default='pending', max_length=20)),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('currency', models.CharField(default='UAH', max_length=10)),
                ('recipient_name', models.CharField(blank=True, max_length=200)),
                ('recipient_phone', models.CharField(blank=True, max_length=50)),
                ('recipient_city', models.CharField(blank=True, max_length=100)),
                ('recipient_email', models.EmailField(blank=True, max_length=254)),
                ('comment', models.TextField(blank=True)),
                ('stripe_session_id', models.CharField(blank=True, db_index=True, max_length=255)),
                ('stripe_payment_intent_id', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Замовлення',
                'verbose_name_plural': 'Замовлення',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(max_length=300)),
                ('qty', models.PositiveIntegerField(default=1)),
                ('unit_price', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='bikes.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='order_items', to='bikes.product')),
            ],
            options={
                'verbose_name': 'Позиція замовлення',
                'verbose_name_plural': 'Позиції замовлення',
            },
        ),
    ]

