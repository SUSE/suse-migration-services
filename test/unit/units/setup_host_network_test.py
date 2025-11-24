from unittest.mock import (
    patch, call, Mock
)
from pytest import raises

from suse_migration_services.units.setup_host_network import (
    main, container, SetupHostNetwork
)
from suse_migration_services.exceptions import (
    DistMigrationHostNetworkException
)
from suse_migration_services.defaults import Defaults


class TestSetupHostNetwork:
    @patch('suse_migration_services.logger.Logger.setup')
    def setup(self, mock_Logger_setup):
        self.host_network = SetupHostNetwork()
        self.host_network.root_path = '/system-root'

    @patch('suse_migration_services.logger.Logger.setup')
    def setup_method(self, cls, mock_Logger_setup):
        self.setup()

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
    def test_container(
        self,
        mock_isfile,
        mock_glob,
        mock_shutil_copy,
        mock_os_path_exists,
        mock_Fstab,
        mock_Command_run,
        mock_logger_setup,
        mock_get_migration_config_file
    ):
        fstab = Mock()
        mock_Fstab.return_value = fstab
        mock_glob.return_value = [
            '/system-root/etc/sysconfig/network/ifcfg-eth0',
            '/system-root/etc/sysconfig/network/dhcp'
        ]
        mock_isfile.return_value = True
        mock_os_path_exists.return_value = True
        container()

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
                ['rpm', '--query', '--quiet', 'wicked2nm'],
                raise_on_error=False
            ),
            call(
                ['systemctl', 'stop', 'NetworkManager']
            )
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

    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.setup_host_network.Fstab')
    @patch('os.path.exists')
    @patch('shutil.copy')
    @patch('glob.glob')
    @patch('os.path.isfile')
    def test_main(
        self,
        mock_isfile,
        mock_glob,
        mock_shutil_copy,
        mock_os_path_exists,
        mock_Fstab,
        mock_Command_run,
        mock_logger_setup,
        mock_get_migration_config_file
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
    def test_wicked2nm_migrate_no_activation(
        self, mock_MigrationConfig, mock_Command_run, mock_os_path_exists
    ):
        migration_config = Mock()
        migration_config.get_network_info.return_value = False
        mock_MigrationConfig.return_value = migration_config
        cmd_ret_val = Mock(self, returncode=0)
        mock_Command_run.return_value = cmd_ret_val
        mock_os_path_exists.return_value = True

        self.host_network.wicked2nm_migrate(
            activate_connections=False
        )
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
                    'wicked2nm',
                    'migrate',
                    '--netconfig-base-dir',
                    '/system-root/etc/sysconfig/network',
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
    def test_wicked2nm_migrate_no_continue(
        self, mock_MigrationConfig, mock_Command_run, mock_os_path_exists
    ):
        migration_config = Mock()
        migration_config.get_network_info.return_value = False
        mock_MigrationConfig.return_value = migration_config
        cmd_ret_val = Mock(self, returncode=0)
        mock_Command_run.return_value = cmd_ret_val
        mock_os_path_exists.return_value = True

        self.host_network.wicked2nm_migrate()
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
                    'wicked2nm',
                    'migrate',
                    '--netconfig-base-dir',
                    '/system-root/etc/sysconfig/network',
                    '--activate-connections',
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

        self.host_network.wicked2nm_migrate()
        mock_os_path_exists.assert_called_once_with(
            '/system-root/var/cache/wicked_config/config.xml'
        )
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

        self.host_network.wicked2nm_migrate()
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
        self, mock_get_migration_config_file,
        mock_Command_run, mock_os_path_exists
    ):
        mock_get_migration_config_file.return_value = \
            '../data/migration-config-wicked2nm.yml'
        cmd_ret_val = Mock(self, returncode=0)
        mock_Command_run.return_value = cmd_ret_val
        cmd_ret_val = Mock(self, returncode=0)
        mock_Command_run.return_value = cmd_ret_val
        mock_os_path_exists.return_value = True

        self.host_network.wicked2nm_migrate()
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
                    'wicked2nm',
                    'migrate',
                    '--netconfig-base-dir',
                    '/system-root/etc/sysconfig/network',
                    '--activate-connections',
                    '/system-root/var/cache/wicked_config/config.xml',
                    '--continue-migration'
                ]
            ),
            call(
                ['nm-online', '-q']
            )
        ]

    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.setup_host_network.MigrationConfig')
    @patch('os.path.exists')
    def test_wicked2nm_migrate_failure(
        self, mock_os_path_exists, mock_MigrationConfig,
        mock_Command_run, mock_logger_setup
    ):
        mock_os_path_exists.return_value = True
        migration_config = Mock()
        migration_config.get_network_info.return_value = False
        mock_MigrationConfig.return_value = migration_config

        def mock_Command_side_effect(
            command, custom_env=None, raise_on_error=True
        ):
            if 'wicked2nm' in command and 'migrate' in command:
                raise Exception
            return Mock(self, returncode=0, output="")
        mock_Command_run.side_effect = mock_Command_side_effect

        with raises(DistMigrationHostNetworkException):
            self.host_network.wicked2nm_migrate()

        assert call(
            [
                'wicked2nm', 'show',
                '--netconfig-base-dir', '/system-root/etc/sysconfig/network',
                '/system-root/var/cache/wicked_config/config.xml'
            ],
            raise_on_error=False
        ) in mock_Command_run.call_args_list
