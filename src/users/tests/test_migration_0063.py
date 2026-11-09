from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

RESULTS = ("django_celery_results", "0014_alter_taskresult_status")
BEFORE = [("users", "0062_drop_notes_public_eu_date_default"), RESULTS]
AFTER = [("users", "0063_rename_yamtrack_import_tasks"), RESULTS]


def migrate(target):
    """Migrate the test database to ``target`` and return the historical apps."""
    executor = MigrationExecutor(connection)
    executor.migrate(target)
    executor.loader.build_graph()
    return executor.loader.project_state(target).apps


class RenameYamtrackImportTasksTests(TransactionTestCase):
    """Import history recorded as "Import from Yamtrack" survives the rename."""

    def tearDown(self):
        """Leave the database fully migrated for the tests that follow."""
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_old_task_results_are_renamed(self):
        """Only the old Yamtrack task name changes."""
        task_result = migrate(BEFORE).get_model("django_celery_results", "TaskResult")
        task_result.objects.create(task_id="a", task_name="Import from Yamtrack")
        task_result.objects.create(task_id="b", task_name="Import from Trakt")

        task_result = migrate(AFTER).get_model("django_celery_results", "TaskResult")

        self.assertEqual(
            sorted(task_result.objects.values_list("task_id", "task_name")),
            [("a", "Import from Magpie"), ("b", "Import from Trakt")],
        )
