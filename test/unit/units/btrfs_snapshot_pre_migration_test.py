import io
from pytest import raises
from unittest.mock import patch, call, MagicMock

from suse_migration_services.units.btrfs_snapshot_pre_migration import main
from suse_migration_services.exceptions import DistMigrationBtrfsSnapshotPreMigrationException


@patch('suse_migration_services.logger.Logger.setup')
class TestMigrationBtrfsSnapshotPre(object):
    @patch('suse_migration_services.command.Command.run')
    @patch('os.path.isfile')
    def test_main(self, mock_os_path_isfile, mock_Command_run, mock_logger_setup):
        mock_os_path_isfile.return_value = True
        snapper_call = MagicMock()
        snapper_call.returncode = 0
        snapper_call.output = '42'
        mock_Command_run.return_value = snapper_call
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.read.return_value = '42'
            main()
            assert mock_Command_run.call_args_list == [
                call(
                    ['chroot', '/system-root', 'snapper', '--no-dbus', 'get-config'],
                    raise_on_error=False,
                ),
                call(
                    [
                        'chroot',
                        '/system-root',
                        'snapper',
                        '--no-dbus',
                        'create',
                        '--from',
                        '42',
                        '--read-only',
                        '--type',
                        'single',
                        '--cleanup-algorithm',
                        'number',
                        '--print-number',
                        '--userdata',
                        'important=yes',
                        '--description',
                        'before offline migration',
                    ]
                ),
            ]
            file_handle.write.assert_called_once_with('42')

    @patch('suse_migration_services.command.Command.run')
    @patch('os.path.isfile')
    def test_main_return_early_no_snapper_config(
        self, mock_os_path_isfile, mock_Command_run, mock_logger_setup
    ):
        mock_os_path_isfile.return_value = False
        snapper_call = MagicMock()
        snapper_call.returncode = 1
        mock_Command_run.return_value = snapper_call
        with patch('builtins.open', create=True):
            main()
            mock_Command_run.assert_called_once_with(
                ['chroot', '/system-root', 'snapper', '--no-dbus', 'get-config'],
                raise_on_error=False,
            )

    @patch('os.path.isfile')
    def test_main_raises(self, mock_os_path_isfile, mock_logger_setup):
        mock_os_path_isfile.side_effect = Exception
        with raises(DistMigrationBtrfsSnapshotPreMigrationException):
            main()
