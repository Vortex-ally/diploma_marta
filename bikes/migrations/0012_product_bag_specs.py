from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bikes', '0011_reviews_for_all_products'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='bag_dimensions',
            field=models.TextField(blank=True, verbose_name='Сумки: розміри'),
        ),
        migrations.AddField(
            model_name='product',
            name='bag_features',
            field=models.TextField(blank=True, help_text='Один пункт на рядок — список у блоці опису', verbose_name='Сумки: особливості'),
        ),
        migrations.AddField(
            model_name='product',
            name='bag_volume',
            field=models.CharField(blank=True, max_length=80, verbose_name='Сумки: обсяг'),
        ),
        migrations.AddField(
            model_name='product',
            name='bag_weight_note',
            field=models.CharField(blank=True, max_length=80, verbose_name='Сумки: вага (текст)'),
        ),
    ]
