# Generated by Django 2.2 on 2021-03-09 06:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_item_discount_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='description',
            field=models.TextField(default="This is a test description. We are trying to see what comes out of it. Don't be confused, we will get there."),
            preserve_default=False,
        ),
    ]