from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bikes', '0015_userprofile_photo'),
    ]

    operations = [
        migrations.AddField(
            model_name='trail',
            name='latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='trail',
            name='longitude',
            field=models.FloatField(blank=True, null=True),
        ),
    ]

