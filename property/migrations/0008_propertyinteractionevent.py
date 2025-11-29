from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('property', '0007_property_is_roomie_listing_property_roomie_profile'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='PropertyInteractionEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('back', 'Volver atrás')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('property', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interaction_events', to='property.property')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='property_interaction_events', to='auth.user')),
            ],
        ),
        migrations.AddIndex(
            model_name='propertyinteractionevent',
            index=models.Index(fields=['user', 'event_type', 'created_at'], name='prop_inter_user_event_idx'),
        ),
    ]

