# Generated by Django 5.1.5 on 2025-02-08 01:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendor',
            name='image',
            field=models.FileField(blank=True, default='default/vendor.jpg', null=True, upload_to='vendor'),
        ),
    ]
