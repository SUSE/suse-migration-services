import io
from unittest.mock import (
    patch, call, Mock, MagicMock
)

from pytest import raises

from suse_migration_services.units.prepare import main
from suse_migration_services.fstab import Fstab
from suse_migration_services.exceptions import (
    DistMigrationZypperMetaDataException,
    DistMigrationLoggingException
)


class TestSetupPrepare(object):
    @patch('suse_migration_services.logger.log.error')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.prepare.Fstab')
    @patch('os.path.exists')
    @patch('shutil.copy')
    @patch('os.listdir')
    def test_main_raises_on_zypp_bind(
        self, mock_os_listdir, mock_shutil_copy, mock_os_path_exists,
        mock_Fstab, mock_Command_run,
        mock_info, mock_error
    ):
        mock_os_listdir.return_value = None
        mock_os_path_exists.return_value = True
        mock_Command_run.side_effect = Exception
        with raises(DistMigrationZypperMetaDataException):
            main()
            assert mock_info.called
            assert mock_error.called

    @patch('suse_migration_services.logger.log.error')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.prepare.Fstab')
    @patch('os.path.exists')
    @patch('shutil.copy')
    @patch('os.listdir')
    def test_main_raises_on_log_init(
        self, mock_os_listdir, mock_shutil_copy, mock_os_path_exists,
        mock_Fstab, mock_Command_run, mock_log_info,
        mock_log_error
    ):
        mock_os_path_exists.return_value = True
        with patch('builtins.open', create=True) as mock_open:
            mock_open.side_effect = Exception
            with raises(DistMigrationLoggingException):
                main()
                assert mock_log_info.called
                assert mock_log_error.called

    @patch('suse_migration_services.logger.log.error')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.prepare.Fstab')
    @patch('os.path.exists')
    @patch('shutil.copy')
    @patch('os.listdir')
    def test_main_raises_and_umount_file_system(
        self, mock_os_listdir, mock_shutil_copy, mock_os_path_exists,
        mock_Fstab, mock_Command_run,
        mock_info, mock_error
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
                call(['umount', '/system-root/sys'], raise_on_error=False),
                call(['umount', '/system-root/proc'], raise_on_error=False),
                call(['umount', '/system-root/dev'], raise_on_error=False)
            ]

    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.prepare.Fstab')
    @patch('suse_migration_services.units.prepare.log.set_logfile')
    @patch('os.path.exists')
    @patch('shutil.copy')
    @patch('os.listdir')
    def test_main(
        self, mock_os_listdir, mock_shutil_copy, mock_os_path_exists,
        mock_set_logfile, mock_Fstab, mock_Command_run, mock_info
    ):
        fstab = Mock()
        mock_Fstab.return_value = fstab
        mock_os_listdir.return_value = ['foo', 'bar']
        mock_os_path_exists.return_value = True
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            main()
            assert mock_shutil_copy.call_args_list == [
                call('/system-root/etc/SUSEConnect', '/etc/SUSEConnect'),
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
            assert mock_Command_run.call_args_list == [
                call(
                    [
                        'update-ca-certificates'
                    ]
                ),
                call(
                    [
                        'mount', '--bind', '/system-root/etc/zypp',
                        '/etc/zypp'
                    ]
                ),
                call(
                    [
                        'mount', '-t', 'devtmpfs', 'devtmpfs',
                        '/system-root/dev'
                    ]
                ),
                call(
                    [
                        'mount', '-t', 'proc', 'proc',
                        '/system-root/proc'
                    ]
                ),
                call(
                    [
                        'mount', '-t', 'sysfs', 'sysfs',
                        '/system-root/sys'
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
                    'devtmpfs', '/system-root/dev'
                ),
                call(
                    '/proc', '/system-root/proc'
                ),
                call(
                    'sysfs', '/system-root/sys'
                )
            ]
            fstab.export.assert_called_once_with(
                '/etc/system-root.fstab'
            )
            mock_open.assert_called_once_with(
                '/system-root/var/log/zypper_migrate.log', 'w'
            )
            mock_set_logfile.assert_called_once_with(
                '/system-root/var/log/zypper_migrate.log'
            )
            assert mock_info.called
