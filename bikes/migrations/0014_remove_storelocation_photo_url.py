from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bikes', '0013_storelocation_photo_url'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='storelocation',
            name='photo_url',
        ),
    ]
