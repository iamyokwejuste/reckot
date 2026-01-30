from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0003_alter_reportexport_format_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="reportexport",
            index=models.Index(
                fields=["created_by", "created_at"], name="export_user_created_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="reportexport",
            index=models.Index(
                fields=["event", "report_type", "created_at"],
                name="export_event_type_idx",
            ),
        ),
    ]
