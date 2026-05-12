from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('bikes', '0018_orders_and_payments'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RidePost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('city', models.CharField(max_length=120)),
                ('start_at', models.DateTimeField()),
                ('distance_km', models.FloatField(blank=True, null=True)),
                ('pace', models.CharField(blank=True, max_length=80)),
                ('ride_type', models.CharField(choices=[('road', 'Шосе'), ('mtb', 'MTB'), ('city', 'Місто'), ('mixed', 'Змішано')], default='mixed', max_length=20)),
                ('level', models.CharField(choices=[('easy', 'Легко'), ('medium', 'Середньо'), ('fast', 'Швидко')], default='medium', max_length=20)),
                ('note', models.TextField(blank=True)),
                ('contact_handle', models.CharField(blank=True, max_length=200)),
                ('is_active', models.BooleanField(default=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ride_posts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Пошук напарника',
                'verbose_name_plural': 'Пошук напарника',
                'ordering': ['-is_featured', '-start_at', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='UserSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tier', models.CharField(choices=[('free', 'Free'), ('premium', 'Premium')], default='free', max_length=20)),
                ('status', models.CharField(choices=[('active', 'Активна'), ('past_due', 'Проблема з оплатою'), ('canceled', 'Скасована'), ('incomplete', 'Не завершено')], default='active', max_length=20)),
                ('stripe_customer_id', models.CharField(blank=True, max_length=255)),
                ('stripe_subscription_id', models.CharField(blank=True, db_index=True, max_length=255)),
                ('current_period_end', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Підписка',
                'verbose_name_plural': 'Підписки',
            },
        ),
        migrations.CreateModel(
            name='RideRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Очікує'), ('accepted', 'Прийнято'), ('declined', 'Відхилено'), ('cancelled', 'Скасовано')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests', to='bikes.ridepost')),
                ('requester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ride_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Заявка на катання',
                'verbose_name_plural': 'Заявки на катання',
                'ordering': ['-created_at'],
                'unique_together': {('post', 'requester')},
            },
        ),
    ]

