from django.db import migrations


def rename(old, new):
    """Keep CSV import history recorded under the task's previous name visible."""

    def run(apps, schema_editor):
        TaskResult = apps.get_model("django_celery_results", "TaskResult")
        TaskResult.objects.filter(task_name=old).update(task_name=new)

    return run


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0062_drop_notes_public_eu_date_default"),
        ("django_celery_results", "0014_alter_taskresult_status"),
    ]

    operations = [
        migrations.RunPython(
            rename("Import from Yamtrack", "Import from Magpie"),
            rename("Import from Magpie", "Import from Yamtrack"),
        ),
    ]
