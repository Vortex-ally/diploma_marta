from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bikes', '0012_product_bag_specs'),
    ]

    operations = [
        migrations.AddField(
            model_name='storelocation',
            name='photo_url',
            field=models.URLField(blank=True, verbose_name='Фото точки'),
        ),
    ]
