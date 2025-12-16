
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('user', '0007_alter_userprofile_id_card_back_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='profile_picture_url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='id_card_front_url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='id_card_back_url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='selfie_url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='profilepicturehistory',
            name='image_url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
