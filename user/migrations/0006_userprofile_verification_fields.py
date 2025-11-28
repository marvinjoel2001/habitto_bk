from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0005_userprofile_agent_commission_rate_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='id_card_front',
            field=models.ImageField(blank=True, null=True, upload_to='verification_docs'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='id_card_back',
            field=models.ImageField(blank=True, null=True, upload_to='verification_docs'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='selfie',
            field=models.ImageField(blank=True, null=True, upload_to='verification_docs'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='document_number',
            field=models.CharField(blank=True, null=True, max_length=50),
        ),
    ]
