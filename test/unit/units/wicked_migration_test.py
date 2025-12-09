from pytest import raises
from unittest.mock import (
    patch, call
)

from suse_migration_services.drop_components import DropComponents
from suse_migration_services.units.wicked_migration import main, WickedToNetworkManager
from suse_migration_services.exceptions import (
    DistMigrationWickedMigrationException
)


class TestMigrationWicked:
    @patch('os.readlink')
    @patch('os.path.exists')
    @patch.object(DropComponents, 'drop_package')
    @patch.object(DropComponents, 'drop_perform')
    @patch.object(DropComponents, 'package_installed')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('glob.iglob')
    def test_main(
        self,
        mock_iglob,
        mock_Command_run,
        mock_logger_setup,
        mock_package_installed,
        mock_drop_perform,
        mock_drop_package,
        mock_os_exists,
        mock_os_readlink,
    ):
        mock_package_installed.return_value = True
        mock_iglob.return_value = [
            '/etc/NetworkManager/system-connections/some.nmconnection'
        ]
        mock_os_readlink.return_value = '/usr/lib/systemd/system/wicked.service'
        main()
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'systemctl', '--root', '/system-root',
                    'enable', '--force', 'NetworkManager.service'
                ]
            ),
            call(
                [
                    'systemctl', '--root', '/system-root',
                    'mask', 'wicked.service'
                ]
            ),
            call(
                [
                    'mkdir', '-p',
                    '/system-root/etc/NetworkManager/system-connections'
                ]
            ),
            call(
                [
                    'cp',
                    '/etc/NetworkManager/system-connections/some.nmconnection',
                    '/system-root/etc/NetworkManager/system-connections'
                ]
            )
        ]
        assert mock_drop_package.call_args_list == [
            call('wicked'),
            call('wicked-service'),
            call('biosdevname'),
        ]
        mock_drop_perform.assert_called_once_with()

    @patch('os.readlink')
    @patch('os.path.exists')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('glob.iglob')
    def test_is_wicked_enabled(
        self,
        mock_iglob,
        mock_Command_run,
        mock_logger_setup,
        mock_os_exists,
        mock_os_readlink,
    ):
        network_migration = WickedToNetworkManager()

        mock_os_readlink.return_value = '/etc/systemd/system/NetworkManager.service'
        assert not network_migration.is_wicked_enabled()

        mock_os_readlink.return_value = '/etc/systemd/system/wicked.service'
        assert network_migration.is_wicked_enabled()

    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    def test_main_raises(
        self, mock_Command_run, mock_logger_setup
    ):
        mock_Command_run.side_effect = Exception
        with raises(DistMigrationWickedMigrationException):
            main()
