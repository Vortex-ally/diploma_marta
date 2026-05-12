# Заповнення відгуків для всіх товарів, у яких їх ще немає (раніше 0008 обмежувався 40 позиціями).

from django.db import migrations


def _recompute(Product, product_id):
    p = Product.objects.filter(pk=product_id).first()
    if not p:
        return
    qs = p.reviews.all()
    cnt = qs.count()
    if cnt == 0:
        p.rating = 0.0
        p.reviews_count = 0
    else:
        total = sum(int(r.rating) for r in qs)
        p.rating = round(total / cnt, 2)
        p.reviews_count = cnt
    p.save(update_fields=['rating', 'reviews_count'])


def forwards(apps, schema_editor):
    Product = apps.get_model('bikes', 'Product')
    Review = apps.get_model('bikes', 'Review')

    rows = [
        ('Оля', 5, 'Швидка доставка, все як на сайті. Рекомендую.'),
        ('Андрій', 4, 'Якість гарна; є дрібниці, але загалом задоволений.'),
        ('Марія', 5, 'Комфортно користуватися, розмір підійшов.'),
        ('Ігор', 5, 'Для своїх грошей — топ. Буду ще замовляти.'),
        ('Наталя', 4, 'Норм товар, фото відповідає реальності.'),
        ('Дмитро', 5, 'Усе ок, підтримка відповіла на питання до покупки.'),
    ]
    n = len(rows)

    for p in Product.objects.all().iterator():
        if Review.objects.filter(product_id=p.id).exists():
            continue
        i = p.id % n
        j = (p.id // 3 + 1) % n
        if j == i:
            j = (i + 1) % n
        for author, rating, text in (rows[i], rows[j]):
            Review.objects.create(product_id=p.id, author=author, rating=rating, text=text)
        _recompute(Product, p.id)


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('bikes', '0010_backfill_product_images'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
