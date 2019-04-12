from unittest.mock import (
    patch, Mock
)
from pytest import raises

from suse_migration_services.units.setup_host_network import main
from suse_migration_services.exceptions import (
    DistMigrationNameResolverException,
    DistMigrationHostNetworkException
)


class TestSetupHostNetwork(object):
    @patch('suse_migration_services.logger.log.error')
    @patch('os.path.exists')
    def test_main_resolv_conf_not_present(
        self, mock_os_path_exists, mock_error
    ):
        mock_os_path_exists.return_value = False
        with raises(DistMigrationNameResolverException):
            main()
            assert mock_error.called

    @patch('suse_migration_services.logger.log.error')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.setup_host_network.Fstab')
    @patch('os.path.exists')
    @patch('shutil.copy')
    def test_main_raises_on_host_network_activation(
        self, mock_shutil_copy, mock_os_path_exists,
        mock_Fstab, mock_Command_run, mock_info,
        mock_error
    ):
        mock_os_path_exists.return_value = True
        mock_Command_run.side_effect = Exception
        with raises(DistMigrationHostNetworkException):
            main()
            assert mock_error.called

    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.setup_host_network.Fstab')
    @patch('os.path.exists')
    @patch('shutil.copy')
    def test_main(
        self, mock_shutil_copy, mock_os_path_exists,
        mock_Fstab, mock_Command_run, mock_info
    ):
        fstab = Mock()
        mock_Fstab.return_value = fstab
        mock_os_path_exists.return_value = True
        main()
        mock_shutil_copy.assert_called_once_with(
            '/system-root/etc/resolv.conf', '/etc/resolv.conf'
        )
        mock_Command_run.assert_called_once_with(
            [
                'mount', '--bind', '/system-root/etc/sysconfig/network',
                '/etc/sysconfig/network'
            ]
        )
        fstab.read.assert_called_once_with(
            '/etc/system-root.fstab'
        )
        fstab.add_entry.assert_called_once_with(
            '/system-root/etc/sysconfig/network', '/etc/sysconfig/network'
        )
        fstab.export.assert_called_once_with(
            '/etc/system-root.fstab'
        )
