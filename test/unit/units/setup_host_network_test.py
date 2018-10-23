from unittest.mock import (
    patch, call
)
from pytest import raises

from suse_migration_services.units.setup_host_network import main
from suse_migration_services.exceptions import (
    DistMigrationNameResolverException,
    DistMigrationHostNetworkException
)


class TestSetupHostNetwork(object):
    @patch('os.path.exists')
    def test_main_resolv_conf_not_present(self, mock_os_path_exists):
        mock_os_path_exists.return_value = False
        with raises(DistMigrationNameResolverException):
            main()

    @patch('suse_migration_services.command.Command.run')
    @patch('os.path.exists')
    @patch('shutil.copy')
    def test_main_raises_on_host_network_activation(
        self, mock_shutil_copy, mock_os_path_exists, mock_Command_run
    ):
        mock_os_path_exists.return_value = True
        mock_Command_run.side_effect = Exception
        with raises(DistMigrationHostNetworkException):
            main()

    @patch('suse_migration_services.command.Command.run')
    @patch('os.path.exists')
    @patch('shutil.copy')
    def test_main(
        self, mock_shutil_copy, mock_os_path_exists, mock_Command_run
    ):
        mock_os_path_exists.return_value = True
        main()
        mock_shutil_copy.assert_called_once_with(
            '/system-root/etc/resolv.conf', '/etc/resolv.conf'
        )
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'mount', '--bind', '/system-root/etc/sysconfig/network',
                    '/etc/sysconfig/network'
                ]
            ),
            call(
                ['systemctl', 'daemon-reload']
            ),
            call(
                ['systemctl', 'restart', 'network']
            )
        ]
