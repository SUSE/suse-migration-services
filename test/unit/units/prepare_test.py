from unittest.mock import (
    patch, call
)
from pytest import raises

from suse_migration_services.units.prepare import main
from suse_migration_services.exceptions import (
    DistMigrationSUSEConnectException,
    DistMigrationZypperMetaDataException
)


class TestSetupPrepare(object):
    @patch('os.path.exists')
    def test_main_suseconnect_not_present(self, mock_os_path_exists):
        mock_os_path_exists.return_value = False
        with raises(DistMigrationSUSEConnectException):
            main()

    @patch('suse_migration_services.command.Command.run')
    @patch('os.path.exists')
    @patch('shutil.copy')
    def test_main_raises_on_zypp_bind(
        self, mock_shutil_copy, mock_os_path_exists, mock_Command_run
    ):
        mock_os_path_exists.return_value = True
        mock_Command_run.side_effect = Exception
        with raises(DistMigrationZypperMetaDataException):
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
