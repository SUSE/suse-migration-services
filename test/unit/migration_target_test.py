from unittest.mock import (
    patch, Mock
)

from suse_migration_services.migration_target import MigrationTarget


class TestMigrationTarget(object):
    @patch('platform.machine')
    @patch('os.path.isfile')
    @patch('suse_migration_services.command.Command.run')
    def test_get_migration_target(
        self, mock_Command_run, mock_os_path_isfile,
        mock_platform_machine
    ):
        mock_platform_machine.return_value = 'x86_64'
        sles15_migration = Mock()
        sles15_migration.returncode = 0
        mock_Command_run.return_value = sles15_migration
        mock_os_path_isfile.return_value = False
        assert MigrationTarget.get_migration_target() == {
            'identifier': 'SLES',
            'version': '15.3',
            'arch': 'x86_64'
        }

    @patch('platform.machine')
    @patch('os.path.isfile')
    @patch('suse_migration_services.command.Command.run')
    def test_get_migration_target_sles16(
        self, mock_Command_run, mock_os_path_isfile,
        mock_platform_machine
    ):
        mock_platform_machine.return_value = 'x86_64'
        sles15_migration_not_found = Mock()
        sles15_migration_not_found.returncode = 1  # SLES15-Migration not found
        sles16_migration_found = Mock()
        sles16_migration_found.returncode = 0  # SLES16-Migration found
        mock_Command_run.side_effect = [sles15_migration_not_found, sles16_migration_found]
        mock_os_path_isfile.return_value = False  # No /etc/sle-migration-service.yml
        assert MigrationTarget.get_migration_target() == {
            'identifier': 'SLES',
            'version': '16.0',
            'arch': 'x86_64'
        }
