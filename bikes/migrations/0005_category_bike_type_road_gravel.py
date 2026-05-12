# Generated manually for road/gravel bike types

from django.db import migrations, models


def migrate_mens_womens_to_road_gravel(apps, schema_editor):
    Category = apps.get_model('bikes', 'Category')
    Category.objects.filter(bike_type='mens').update(
        bike_type='road',
        slug='road',
        name='Шосейні велосипеди',
    )
    Category.objects.filter(bike_type='womens').update(
        bike_type='gravel',
        slug='gravel',
        name='Гравійні велосипеди',
    )


def reverse_migrate(apps, schema_editor):
    Category = apps.get_model('bikes', 'Category')
    Category.objects.filter(bike_type='road').update(
        bike_type='mens',
        slug='mens',
        name='Чоловічі велосипеди',
    )
    Category.objects.filter(bike_type='gravel').update(
        bike_type='womens',
        slug='womens',
        name='Жіночі велосипеди',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('bikes', '0004_userprofile'),
    ]

    operations = [
        migrations.RunPython(migrate_mens_womens_to_road_gravel, reverse_migrate),
        migrations.AlterField(
            model_name='category',
            name='bike_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('road', 'Шосейні'),
                    ('gravel', 'Гравійні'),
                    ('kids', 'Дитячі'),
                    ('electric', 'Електровелосипеди'),
                ],
                max_length=20,
                null=True,
            ),
        ),
    ]
