from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bikes', '0016_trail_coordinates'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trail',
            name='image_url',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]

