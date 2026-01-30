from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_refund_refundauditlog_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['status', 'expires_at'], name='payment_status_expires_idx'),
        ),
        migrations.AddIndex(
            model_name='withdrawal',
            index=models.Index(fields=['organization', 'status', 'created_at'], name='withdrawal_org_status_idx'),
        ),
        migrations.AddIndex(
            model_name='refund',
            index=models.Index(fields=['status', 'created_at'], name='refund_status_created_idx'),
        ),
    ]
