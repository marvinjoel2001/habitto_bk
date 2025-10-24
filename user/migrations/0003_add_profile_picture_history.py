# Generated manually for profile picture history functionality

from django.db import migrations, models
import django.db.models.deletion
import user.models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_userprofile_profile_picture'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to=user.models.user_profile_picture_path),
        ),
        migrations.CreateModel(
            name='ProfilePictureHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to=user.models.user_profile_picture_path)),
                ('original_filename', models.CharField(max_length=255)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('is_current', models.BooleanField(default=False)),
                ('user_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='picture_history', to='user.userprofile')),
            ],
            options={
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.AddIndex(
            model_name='profilepicturehistory',
            index=models.Index(fields=['user_profile', 'is_current'], name='user_profile_current_idx'),
        ),
    ]
