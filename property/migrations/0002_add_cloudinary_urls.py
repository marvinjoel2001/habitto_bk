
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('property', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='photos_urls',
            field=models.JSONField(blank=True, default=list, help_text='Lista de URLs de imágenes en Cloudinary'),
        ),
    ]
