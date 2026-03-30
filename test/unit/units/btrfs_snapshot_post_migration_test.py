import io
from pytest import raises
from unittest.mock import patch, MagicMock, call

from suse_migration_services.units.btrfs_snapshot_post_migration import main
from suse_migration_services.exceptions import DistMigrationBtrfsSnapshotPostMigrationException


@patch('suse_migration_services.logger.Logger.setup')
class TestMigrationBtrfsSnapshotPost(object):
    @patch('suse_migration_services.command.Command.run')
    def test_main_not_btrfs(self, mock_Command_run, mock_logger_setup):
        mock_Command_run.return_value.returncode = 0
        mock_Command_run.return_value.output = 'ext4'
        main()
        mock_Command_run.assert_called_once_with(['stat', '-f', '-c', '%T', '/system-root'])

    @patch('suse_migration_services.command.Command.run')
    def test_main(self, mock_Command_run, mock_logger_setup):
        def command_run_callback(*args, **kwargs):
            snapper_call = MagicMock()
            if args[0][0] == 'stat':
                snapper_call = MagicMock()
                snapper_call.returncode = 0
                snapper_call.output = 'btrfs'
            else:
                snapper_call.returncode = 0
                snapper_call.output = '42'
            return snapper_call

        mock_Command_run.side_effect = command_run_callback

        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.read.return_value = b'42'
            main()
        assert mock_Command_run.call_args_list == [
            call(['stat', '-f', '-c', '%T', '/system-root']),
            call(
                [
                    'chroot',
                    '/system-root',
                    'snapper',
                    '--no-dbus',
                    'create',
                    '--type',
                    'single',
                    '--read-only',
                    '--cleanup-algorithm',
                    'number',
                    '--print-number',
                    '--userdata',
                    'important=yes',
                    '--description',
                    'after offline migration',
                ]
            ),
        ]

    @patch('suse_migration_services.command.Command.run')
    def test_main_raises_on_snapper(self, mock_Command_run, mock_logger_setup):
        mock_Command_run.side_effect = Exception
        with raises(DistMigrationBtrfsSnapshotPostMigrationException):
            with patch('builtins.open', create=True):
                main()

    @patch('suse_migration_services.command.Command.run')
    def test_main_raises_on_invalid_snapshot_number(self, mock_Command_run, mock_logger_setup):
        def command_run_callback(*args, **kwargs):
            snapper_call = MagicMock()
            if args[0][0] == 'stat':
                snapper_call = MagicMock()
                snapper_call.returncode = 0
                snapper_call.output = 'btrfs'
            else:
                snapper_call.returncode = 0
                snapper_call.output = '42'
            return snapper_call

        mock_Command_run.side_effect = command_run_callback
        with raises(DistMigrationBtrfsSnapshotPostMigrationException):
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value = MagicMock(spec=io.IOBase)
                file_handle = mock_open.return_value.__enter__.return_value
                file_handle.read.return_value = b'bogus'
                main()
