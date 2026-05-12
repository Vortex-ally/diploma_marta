from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bikes', '0014_remove_storelocation_photo_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='profiles/', verbose_name='Фото профілю'),
        ),
    ]

