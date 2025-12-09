from django.db import migrations, models
import django.db.models.deletion
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0010_userprofile_soft_delete_fields'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserLocationPoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='location_points', to='auth.user')),
            ],
        ),
        migrations.AddIndex(
            model_name='userlocationpoint',
            index=models.Index(fields=['user', 'created_at'], name='user_loc_user_created_idx'),
        ),
    ]

