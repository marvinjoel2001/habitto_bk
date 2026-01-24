from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matching', '0003_searchprofile_stable_job'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchprofile',
            name='work_location',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='searchprofile',
            name='children_school',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='searchprofile',
            name='university',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='searchprofile',
            name='recurring_places',
            field=models.JSONField(default=list),
        ),
    ]
