# Generated by Django 4.2.16 on 2024-11-28 01:27

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_alter_lostitem_product'),
    ]

    operations = [
        migrations.AddField(
            model_name='lostitem',
            name='expire_at',
            field=models.DateTimeField(default=datetime.datetime(2024, 12, 28, 1, 27, 41, 113718, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
    ]
