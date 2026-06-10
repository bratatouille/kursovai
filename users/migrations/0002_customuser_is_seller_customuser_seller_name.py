from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='is_seller',
            field=models.BooleanField(default=False, verbose_name='seller account'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='seller_name',
            field=models.CharField(blank=True, max_length=150, verbose_name='seller store name'),
        ),
    ]
