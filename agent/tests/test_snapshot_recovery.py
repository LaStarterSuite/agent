from __future__ import annotations

import unittest
from unittest.mock import patch

from agent.snapshot_recovery import SnapshotRecovery


class TestBackupDB(unittest.TestCase):
    """The MariaDB root password must never sit on the dump command line."""

    def setUp(self):
        self.recovery = SnapshotRecovery.__new__(SnapshotRecovery)

    def run_backup_db(self, file_path):
        with patch("agent.snapshot_recovery.db_dump_cli", return_value="mariadb-dump"), patch(
            "agent.snapshot_recovery.subprocess.run"
        ) as run:
            SnapshotRecovery._backup_db.__wrapped__(
                self.recovery,
                "site.local",
                "127.0.0.1",
                "site_database",
                "root-password",
                file_path,
            )
        return run.call_args

    def test_the_root_password_travels_through_the_environment_not_the_command(self):
        call = self.run_backup_db("/benches/site_local.sql.gz")

        self.assertNotIn("root-password", call.args[0])
        self.assertEqual(call.kwargs["env"]["MYSQL_PWD"], "root-password")

    def test_interpolated_paths_are_quoted_against_the_shell(self):
        call = self.run_backup_db("/benches/backups dir/site_local.sql.gz")

        self.assertNotIn("root-password", call.args[0])
        self.assertIn("'/benches/backups dir/site_local.sql.gz'", call.args[0])
        self.assertTrue(call.kwargs["shell"])
        self.assertTrue(call.kwargs["check"])
