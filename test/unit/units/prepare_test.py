from unittest.mock import (
    patch, call, Mock, MagicMock
)

from pytest import raises

from suse_migration_services.units.prepare import main
from suse_migration_services.suse_connect import SUSEConnect
from suse_migration_services.fstab import Fstab
from suse_migration_services.exceptions import (
    DistMigrationZypperMetaDataException
)


class TestSetupPrepare(object):
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.prepare.Fstab')
    @patch('os.path.exists')
    @patch('shutil.copy')
    @patch('os.listdir')
    def test_main_raises_on_zypp_bind(
        self, mock_os_listdir, mock_shutil_copy, mock_os_path_exists,
        mock_Fstab, mock_Command_run, mock_logger_setup
    ):
        mock_os_listdir.return_value = None
        mock_os_path_exists.return_value = True
        mock_Command_run.side_effect = [
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            Exception
        ]
        with raises(DistMigrationZypperMetaDataException):
            main()

    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.prepare.Fstab')
    @patch('os.path.exists')
    @patch('shutil.copy')
    @patch('os.listdir')
    def test_main_raises_and_umount_file_system(
        self, mock_os_listdir, mock_shutil_copy, mock_os_path_exists,
        mock_Fstab, mock_Command_run, mock_logger_setup
    ):
        fstab = Fstab()
        fstab_mock = Mock()
        fstab_mock.read.return_value = fstab.read('../data/bind-mounted.fstab')
        fstab_mock.get_devices.return_value = fstab.get_devices()
        fstab_mock.export.side_effect = Exception
        mock_Fstab.return_value = fstab_mock
        mock_os_path_exists.return_value = True
        with raises(DistMigrationZypperMetaDataException):
            main()
            assert mock_Command_run.call_args_list == [
                call(['ip', 'a'], raise_on_error=False),
                call(['ip', 'r'], raise_on_error=False),
                call(['cat', '/etc/resolv.conf'], raise_on_error=False),
                call(['cat', '/proc/net/bonding/bond*'], raise_on_error=False),
                call(['umount', '/system-root/sys'], raise_on_error=False),
                call(['umount', '/system-root/proc'], raise_on_error=False),
                call(['umount', '/system-root/dev'], raise_on_error=False)
            ]

    @patch.object(SUSEConnect, 'is_registered')
    @patch('suse_migration_services.units.prepare.MigrationConfig')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.prepare.Fstab')
    @patch('suse_migration_services.units.prepare.Path')
    @patch('os.path.exists')
    @patch('shutil.copy')
    @patch('os.listdir')
    def test_main(
        self, mock_os_listdir, mock_shutil_copy, mock_os_path_exists,
        mock_Path, mock_Fstab, mock_Command_run, mock_logger_setup,
        mock_MigrationConfig, mock_is_registered
    ):
        migration_config = Mock()
        migration_config.is_zypper_migration_plugin_requested.return_value = \
            True
        mock_MigrationConfig.return_value = migration_config
        fstab = Mock()
        mock_Fstab.return_value = fstab
        mock_os_listdir.return_value = ['foo', 'bar']
        mock_os_path_exists.side_effect = [True, True, True, True,
                                           True, False, True, True]
        mock_is_registered.return_value = True
        mock_Command_run.side_effect = [
            MagicMock(),
            Exception('no zypper log'),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock()
        ]
        with patch('builtins.open', create=True):
            main()
        assert mock_shutil_copy.call_args_list == [
            call('/system-root/etc/SUSEConnect', '/etc/SUSEConnect'),
            call(
                '/system-root/etc/regionserverclnt.cfg',
                '/etc/regionserverclnt.cfg'
            ),
            call('/system-root/etc/hosts', '/etc/hosts'),
            call(
                '/system-root/usr/share/pki/trust/anchors/foo',
                '/usr/share/pki/trust/anchors/'
            ),
            call(
                '/system-root/usr/share/pki/trust/anchors/bar',
                '/usr/share/pki/trust/anchors/'
            )
        ]
        mock_Path.create.assert_called_once_with(
            '/var/lib/cloudregister'
        )
        assert mock_Command_run.call_args_list == [
            call(
                ['update-ca-certificates']
            ),
            call(
                [
                    'mount', '--bind', '/system-root/var/log/zypper.log',
                    '/var/log/zypper.log'
                ]
            ),
            call(
                ['ip', 'a'], raise_on_error=False
            ),
            call(
                ['ip', 'r'], raise_on_error=False
            ),
            call(
                ['cat', '/etc/resolv.conf'], raise_on_error=False
            ),
            call(
                ['cat', '/proc/net/bonding/bond*'], raise_on_error=False
            ),
            call(
                ['mount', '--bind', '/system-root/etc/zypp', '/etc/zypp']
            ),
            call(
                [
                    'mount', '--bind',
                    '/system-root/usr/lib/zypp/plugins/services',
                    '/usr/lib/zypp/plugins/services'
                ]
            ),
            call(
                [
                    'mount', '--bind', '/system-root/var/lib/cloudregister',
                    '/var/lib/cloudregister'
                ]
            )
        ]
        fstab.read.assert_called_once_with(
            '/etc/system-root.fstab'
        )
        assert fstab.add_entry.call_args_list == [
            call(
                '/system-root/etc/zypp', '/etc/zypp'
            ),
            call(
                '/system-root/usr/lib/zypp/plugins/services',
                '/usr/lib/zypp/plugins/services'
            )
        ]
        fstab.export.assert_called_once_with(
            '/etc/system-root.fstab'
        )
        mock_Command_run.assert_any_call(
            ['cat', '/proc/net/bonding/bond*'], raise_on_error=False
        )

    @patch.object(SUSEConnect, 'is_registered')
    @patch('suse_migration_services.units.prepare.MigrationConfig')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.prepare.Fstab')
    @patch('suse_migration_services.units.prepare.Path')
    @patch('os.path.exists')
    @patch('shutil.copy')
    @patch('os.listdir')
    def test_main_no_registered_instance(
        self, mock_os_listdir, mock_shutil_copy, mock_os_path_exists,
        mock_Path, mock_Fstab, mock_Command_run, mock_logger_setup,
        mock_MigrationConfig, mock_is_registered
    ):
        migration_config = Mock()
        migration_config.is_zypper_migration_plugin_requested.return_value = \
            True
        mock_MigrationConfig.return_value = migration_config
        fstab = Mock()
        mock_Fstab.return_value = fstab
        mock_os_listdir.return_value = ['foo', 'bar']
        mock_os_path_exists.return_value = True
        mock_is_registered.return_value = False
        with raises(DistMigrationZypperMetaDataException):
            main()
