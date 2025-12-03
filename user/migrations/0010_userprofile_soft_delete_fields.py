from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0009_rename_user_blocker_blocked_idx_user_block_blocker_24f410_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='deletion_pending',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='deletion_requested_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='deletion_scheduled_for',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

