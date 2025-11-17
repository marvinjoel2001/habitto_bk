from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('message', '0003_message_deleted_for_receiver_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE message_message
            ADD COLUMN IF NOT EXISTS edited boolean NOT NULL DEFAULT false;
            """,
            reverse_sql="""
            ALTER TABLE message_message
            DROP COLUMN IF EXISTS edited;
            """,
        ),
    ]