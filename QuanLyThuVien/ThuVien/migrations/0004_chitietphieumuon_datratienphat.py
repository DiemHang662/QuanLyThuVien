# Generated by Django 5.1.1 on 2024-10-27 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ThuVien', '0003_alter_chitietphieumuon_tinhtrang'),
    ]

    operations = [
        migrations.AddField(
            model_name='chitietphieumuon',
            name='daTraTienPhat',
            field=models.BooleanField(default=False, null=True),
        ),
    ]