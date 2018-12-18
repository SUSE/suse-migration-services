import io
from unittest.mock import (
    patch, call, Mock, MagicMock
)

from pytest import raises

from suse_migration_services.units.prepare import main
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
    def test_main_raises_on_zypp_bind(
        self, mock_shutil_copy, mock_os_path_exists,
        mock_Fstab, mock_Command_run,
        mock_info, mock_error
    ):
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
    def test_main_raises_on_log_init(
        self, mock_shutil_copy, mock_os_path_exists,
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

    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.prepare.Fstab')
    @patch('os.path.exists')
    @patch('shutil.copy')
    def test_main(
        self, mock_shutil_copy, mock_os_path_exists,
        mock_Fstab, mock_Command_run,
        mock_info
    ):
        fstab = Mock()
        mock_Fstab.return_value = fstab
        mock_os_path_exists.return_value = True
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            main()
            mock_shutil_copy.assert_called_once_with(
                '/system-root/etc/SUSEConnect', '/etc/SUSEConnect'
            )
            assert mock_Command_run.call_args_list == [
                call(
                    [
                        'mount', '--bind', '/system-root/etc/zypp',
                        '/etc/zypp'
                    ]
                )
            ]
            fstab.read.assert_called_once_with(
                '/etc/system-root.fstab'
            )
            fstab.add_entry.assert_called_once_with(
                '/system-root/etc/zypp', '/etc/zypp'
            )
            fstab.export.assert_called_once_with(
                '/etc/system-root.fstab'
            )
            mock_open.assert_called_once_with(
                '/system-root/var/log/zypper_migrate.log', 'w'
            )
            assert mock_info.called
