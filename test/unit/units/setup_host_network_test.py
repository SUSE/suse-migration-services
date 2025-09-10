from unittest.mock import (
    patch, call, Mock
)
from pytest import raises

from suse_migration_services.units.setup_host_network import (
    main, wicked2nm_migrate, setup_interfaces
)
from suse_migration_services.exceptions import (
    DistMigrationHostNetworkException
)
from suse_migration_services.defaults import Defaults


class TestSetupHostNetwork(object):
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.setup_host_network.Fstab')
    @patch('os.path.exists')
    @patch('shutil.copy')
    def test_main_raises_on_host_network_activation(
        self, mock_shutil_copy, mock_os_path_exists,
        mock_Fstab, mock_Command_run, mock_logger_setup
    ):
        mock_os_path_exists.return_value = True
        mock_Command_run.side_effect = Exception
        with raises(DistMigrationHostNetworkException):
            main()
        assert not mock_shutil_copy.called

    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.setup_host_network.Fstab')
    @patch('os.path.exists')
    @patch('shutil.copy')
    @patch('glob.glob')
    @patch('os.path.isfile')
    def test_main(
        self, mock_isfile, mock_glob, mock_shutil_copy, mock_os_path_exists,
        mock_Fstab, mock_Command_run, mock_logger_setup, mock_get_migration_config_file
    ):
        fstab = Mock()
        mock_Fstab.return_value = fstab
        mock_glob.return_value = [
            '/system-root/etc/sysconfig/network/ifcfg-eth0',
            '/system-root/etc/sysconfig/network/dhcp'
        ]
        mock_isfile.return_value = True
        mock_os_path_exists.return_value = True
        main()

        mock_glob.assert_called_once_with(
            '/system-root/etc/sysconfig/network/*'
        )
        assert mock_shutil_copy.call_args_list == [
            call(
                '/system-root/etc/sysconfig/network/ifcfg-eth0',
                '/etc/sysconfig/network'
            ),
            call(
                '/system-root/etc/sysconfig/network/dhcp',
                '/etc/sysconfig/network'
            ),
            call(
                '/system-root/var/cache/udev_rules/70-migration-persistent-net.rules',
                '/etc/udev/rules.d/70-migration-persistent-net.rules'
            )
        ]
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'mount', '--bind',
                    '/system-root/etc/sysconfig/network/providers',
                    '/etc/sysconfig/network/providers'
                ]
            ),
            call(
                ['udevadm', 'control', '--reload']
            ),
            call(
                ['udevadm', 'trigger', '--subsystem-match=net', '--action=add']
            ),
            call(
                ['udevadm', 'settle']
            ),
            call(
                ['systemctl', 'reload', 'network']
            ),
            call(
                ['rpm', '--query', '--quiet', 'wicked2nm'],
                raise_on_error=False
            ),
        ]
        fstab.read.assert_called_once_with(
            '/etc/system-root.fstab'
        )
        fstab.add_entry.assert_called_once_with(
            '/system-root/etc/sysconfig/network/providers',
            '/etc/sysconfig/network/providers'
        )
        fstab.export.assert_called_once_with(
            '/etc/system-root.fstab'
        )

    @patch('os.path.exists')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.setup_host_network.MigrationConfig')
    def test_wicked2nm_migrate_no_continue(
            self, mock_MigrationConfig, mock_Command_run, mock_os_path_exists
    ):
        migration_config = Mock()
        migration_config.get_network_info.return_value = False
        mock_MigrationConfig.return_value = migration_config
        cmd_ret_val = Mock(self, returncode=0)
        mock_Command_run.return_value = cmd_ret_val
        mock_os_path_exists.return_value = True

        wicked2nm_migrate(root_path='/system-root')
        assert mock_Command_run.call_args_list == [
            call(
                ['rpm', '--query', '--quiet', 'wicked2nm'],
                raise_on_error=False
            ),
            call(
                ['rpm', '--query', '--quiet', 'NetworkManager-config-server'],
                raise_on_error=False
            ),
            call(
                [
                    'wicked2nm', 'migrate', '--activate-connections',
                    '--netconfig-path', '/system-root/var/cache/wicked_config/config',
                    '--netconfig-dhcp-path', '/system-root/var/cache/wicked_config/dhcp',
                    '/system-root/var/cache/wicked_config/config.xml'
                ]
            ),
            call(
                ['nm-online', '-q']
            )
        ]

    @patch('os.path.exists')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.setup_host_network.MigrationConfig')
    def test_wicked2nm_migrate_no_config(
            self, mock_MigrationConfig, mock_Command_run, mock_os_path_exists
    ):
        migration_config = Mock()
        migration_config.get_network_info.return_value = False
        mock_MigrationConfig.return_value = migration_config
        mock_os_path_exists.return_value = False

        wicked2nm_migrate(root_path='/system-root')
        mock_os_path_exists.assert_called_once_with('/system-root/var/cache/wicked_config/config.xml')
        mock_Command_run.assert_not_called()

    @patch('os.path.exists')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.setup_host_network.MigrationConfig')
    def test_wicked2nm_nm_config_server_not_installed(
            self, mock_MigrationConfig, mock_Command_run, mock_os_path_exists
    ):
        migration_config = Mock()
        migration_config.get_network_info.return_value = False
        mock_MigrationConfig.return_value = migration_config
        mock_os_path_exists.return_value = True
        cmd_ret_val_success = Mock(self, returncode=0)
        cmd_ret_val_fail = Mock(self, returncode=1)
        mock_Command_run.side_effect = [cmd_ret_val_success, cmd_ret_val_fail]

        wicked2nm_migrate(root_path='/system-root')
        assert mock_Command_run.call_args_list == [
            call(
                ['rpm', '--query', '--quiet', 'wicked2nm'],
                raise_on_error=False
            ),
            call(
                ['rpm', '--query', '--quiet', 'NetworkManager-config-server'],
                raise_on_error=False
            )
        ]

    @patch('os.path.exists')
    @patch('suse_migration_services.command.Command.run')
    @patch.object(Defaults, 'get_migration_config_file')
    def test_wicked2nm_migrate_continue(
            self, mock_get_migration_config_file, mock_Command_run, mock_os_path_exists
    ):
        mock_get_migration_config_file.return_value = \
            '../data/migration-config-wicked2nm.yml'
        cmd_ret_val = Mock(self, returncode=0)
        mock_Command_run.return_value = cmd_ret_val
        cmd_ret_val = Mock(self, returncode=0)
        mock_Command_run.return_value = cmd_ret_val
        mock_os_path_exists.return_value = True

        wicked2nm_migrate(root_path='/system-root')
        assert mock_Command_run.call_args_list == [
            call(
                ['rpm', '--query', '--quiet', 'wicked2nm'],
                raise_on_error=False
            ),
            call(
                ['rpm', '--query', '--quiet', 'NetworkManager-config-server'],
                raise_on_error=False
            ),
            call(
                [
                    'wicked2nm', 'migrate', '--activate-connections',
                    '--netconfig-path', '/system-root/var/cache/wicked_config/config',
                    '--netconfig-dhcp-path', '/system-root/var/cache/wicked_config/dhcp',
                    '/system-root/var/cache/wicked_config/config.xml', '--continue-migration'
                ]
            ),
            call(
                ['nm-online', '-q']
            )
        ]

    @patch('os.path.exists')
    def test_setup_interfaces_migration_rules_dont_exist(
            self, mock_os_path_exists
    ):
        mock_os_path_exists.return_value = False

        setup_interfaces(root_path='/system-root')
        mock_os_path_exists.assert_called_once()

    @patch('shutil.copy')
    @patch('suse_migration_services.command.Command.run')
    @patch('os.path.exists')
    def test_setup_interfaces_create_dir(
            self, mock_os_path_exists, mock_Command_run, mock_shutil_copy
    ):
        mock_os_path_exists.side_effect = [True, False]

        setup_interfaces(root_path='/system-root')
        assert mock_os_path_exists.call_args_list == [
            call('/system-root/var/cache/udev_rules/70-migration-persistent-net.rules'),
            call('/etc/udev/rules.d'),
        ]
        mock_shutil_copy.assert_called()
        assert mock_Command_run.call_args_list == [
            call(
                ['mkdir', '-p', '/etc/udev/rules.d']
            ),
            call(
                ['udevadm', 'control', '--reload']
            ),
            call(
                ['udevadm', 'trigger', '--subsystem-match=net', '--action=add']
            ),
            call(
                ['udevadm', 'settle']
            )
        ]
