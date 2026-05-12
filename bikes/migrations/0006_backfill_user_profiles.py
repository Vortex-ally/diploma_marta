from django.db import migrations


def forwards(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('bikes', 'UserProfile')
    for user in User.objects.all():
        UserProfile.objects.get_or_create(user_id=user.pk)


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('bikes', '0005_category_bike_type_road_gravel'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
