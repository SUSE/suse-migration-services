import io
from unittest.mock import patch, Mock, MagicMock

from suse_migration_services.drop_components import DropComponents


class TestDropComponents:
    @patch('suse_migration_services.drop_components.NamedTemporaryFile')
    @patch('suse_migration_services.drop_components.datetime')
    def setup_method(self, cls, mock_datetime, mock_NamedTemporaryFile):
        date = Mock()
        date.strftime.return_value = '2025-12-07'
        mock_datetime.now.return_value = date
        tmpfile = Mock()
        tmpfile.name = 'tmpfile'
        mock_NamedTemporaryFile.return_value = tmpfile
        self.drop = DropComponents()

    def test_drop_package(self):
        self.drop.drop_package('some')
        assert self.drop.drop_packages == ['some']

    @patch('suse_migration_services.drop_components.Command.run')
    def test_package_installed(self, mock_Command_run):
        package_call = Mock()
        package_call.returncode = 0
        mock_Command_run.return_value = package_call
        assert self.drop.package_installed('some') is True
        package_call.returncode = 1
        assert self.drop.package_installed('some_not_installed') is False

    def test_drop_path(self):
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.drop.drop_path('some/')
            mock_open.assert_called_once_with('tmpfile', 'a')
            file_handle.write.assert_called_once_with('some/\n')
        assert self.drop.drop_files_and_directories == ['/system-root/some']

    @patch('suse_migration_services.drop_components.Zypper.run')
    @patch('suse_migration_services.drop_components.Command.run')
    def test_drop_perform_package(self, mock_Command_run, mock_Zypper_run):
        package_call = Mock()
        package_call.returncode = 0
        mock_Command_run.return_value = package_call
        self.drop.drop_package('some')
        self.drop.drop_package('some_other')
        self.drop.drop_perform()
        mock_Zypper_run.assert_called_once_with(
            [
                '--no-cd',
                '--non-interactive',
                '--gpg-auto-import-keys',
                '--root',
                '/system-root',
                'remove',
                '--clean-deps',
                'some',
                'some_other',
            ],
            raise_on_error=False,
        )

    @patch('os.path.isdir')
    @patch('shutil.rmtree')
    @patch('suse_migration_services.drop_components.Command.run')
    @patch('suse_migration_services.drop_components.Path.create')
    def test_drop_perform_directory(
        self,
        mock_Path_create,
        mock_Command_run,
        mock_shutil_rmtree,
        mock_os_path_isdir,
    ):
        mock_os_path_isdir.return_value = True
        with patch('builtins.open', create=True):
            self.drop.drop_path('some/directory/')
        self.drop.drop_perform()
        mock_Path_create.assert_called_once_with('/system-root/var/migration/2025-12-07')
        mock_Command_run.assert_called_once_with(
            [
                'rsync',
                '-avr',
                '--ignore-missing-args',
                '--files-from',
                'tmpfile',
                '/system-root',
                '/system-root/var/migration/2025-12-07/',
            ]
        )
        mock_shutil_rmtree.assert_called_once_with('/system-root/some/directory')

    @patch('os.path.isdir')
    @patch('pathlib.Path')
    @patch('suse_migration_services.drop_components.Command.run')
    @patch('suse_migration_services.drop_components.Path.create')
    def test_drop_perform_file(
        self, mock_Path_create, mock_Command_run, mock_pathlib_Path, mock_os_path_isdir
    ):
        path = Mock()
        mock_pathlib_Path.return_value = path
        mock_os_path_isdir.return_value = False
        with patch('builtins.open', create=True):
            self.drop.drop_path('some/file')
        self.drop.drop_perform()
        mock_Path_create.assert_called_once_with('/system-root/var/migration/2025-12-07')
        mock_Command_run.assert_called_once_with(
            [
                'rsync',
                '-avr',
                '--ignore-missing-args',
                '--files-from',
                'tmpfile',
                '/system-root',
                '/system-root/var/migration/2025-12-07/',
            ]
        )
        mock_pathlib_Path.assert_called_once_with('/system-root/some/file')
        path.unlink.assert_called_once_with(missing_ok=True)
