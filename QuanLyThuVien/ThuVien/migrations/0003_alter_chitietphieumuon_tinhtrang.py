# Generated by Django 5.1.1 on 2024-10-27 08:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ThuVien', '0002_alter_chitietphieumuon_tinhtrang'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chitietphieumuon',
            name='tinhTrang',
            field=models.CharField(choices=[('borrowed', 'Đang mượn'), ('returned', 'Đã trả'), ('late', 'Trễ hạn')], default='borrowed', max_length=10),
        ),
    ]
