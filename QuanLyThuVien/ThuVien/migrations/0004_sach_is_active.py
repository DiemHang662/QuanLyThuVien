# Generated by Django 5.1.1 on 2024-10-17 13:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ThuVien', '0003_alter_chitietphieumuon_sach_alter_phieumuon_docgia'),
    ]

    operations = [
        migrations.AddField(
            model_name='sach',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]