from unittest import TestCase
from unittest.mock import patch

import os

from suse_migration_services.exceptions import DistMigrationException
from suse_migration_services.units import ha_migration
from suse_migration_services.units.ha_migration import HighAvailabilityExtension


@patch('suse_migration_services.logger.Logger.setup')
class TestMigrationHa(TestCase):
    @patch('os.access')
    def test_corosync_conf_exists(self, mock_os_access, mock_logger_setup):
        mock_os_access.return_value = True
        ha_setup = HighAvailabilityExtension()
        self.assertTrue(ha_setup._corosync_conf_exists())
        mock_os_access.assert_called_once_with(
            '/etc/corosync/corosync.conf', os.F_OK
        )

    @patch('suse_migration_services.command.Command.run')
    @patch('os.chroot')
    @patch('suse_migration_services.units.ha_migration.HighAvailabilityExtension._corosync_conf_exists')
    @patch('suse_migration_services.defaults.Defaults.get_system_root_path')
    def test_main(
        self,
        mock_get_system_root_path,
        mock_corosync_conf_exists,
        mock_chroot,
        mock_command_run,
        mock_logger_setup,
    ):
        mock_get_system_root_path.return_value = '/foo'
        mock_corosync_conf_exists.return_value = True
        ha_migration.main()
        mock_chroot.assert_called_once_with('/foo')
        mock_command_run.assert_called_once_with(['crm', 'cluster', 'health', 'sles16', '--local', '--fix'])

    @patch('suse_migration_services.command.Command.run')
    @patch('os.chroot')
    @patch('suse_migration_services.units.ha_migration.HighAvailabilityExtension._corosync_conf_exists')
    @patch('suse_migration_services.defaults.Defaults.get_system_root_path')
    def test_main_no_corosync_conf(
        self,
        mock_get_system_root_path,
        mock_corosync_conf_exists,
        mock_chroot,
        mock_command_run,
        mock_logger_setup,
    ):
        mock_get_system_root_path.return_value = '/foo'
        mock_corosync_conf_exists.return_value = False
        ha_migration.main()
        mock_chroot.assert_called_once_with('/foo')
        mock_command_run.assert_not_called()

    @patch('suse_migration_services.command.Command.run')
    @patch('os.chroot')
    @patch('suse_migration_services.units.ha_migration.HighAvailabilityExtension._corosync_conf_exists')
    @patch('suse_migration_services.defaults.Defaults.get_system_root_path')
    def test_main_failure(
        self,
        mock_get_system_root_path,
        mock_corosync_conf_exists,
        mock_chroot,
        mock_command_run,
        mock_logger_setup,
    ):
        mock_get_system_root_path.return_value = '/foo'
        mock_corosync_conf_exists.return_value = True
        mock_command_run.side_effect = Exception('bar')
        with self.assertRaises(DistMigrationException) as ctx:
            ha_migration.main()
            self.assertEqual('Migration for high availability failed with bar', ctx.exception.message)
        mock_chroot.assert_called_once_with('/foo')
        mock_command_run.assert_called_once_with(['crm', 'cluster', 'health', 'sles16', '--local', '--fix'])
