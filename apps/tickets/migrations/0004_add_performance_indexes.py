from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0003_add_guest_checkout'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='ticket',
            index=models.Index(fields=['is_checked_in', 'booking'], name='ticket_checkin_booking_idx'),
        ),
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['status', 'event'], name='booking_status_event_idx'),
        ),
    ]
