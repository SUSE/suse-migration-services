from unittest.mock import (
    patch, Mock
)

from suse_migration_services.drop_components import DropComponents


class TestDropComponents:
    def setup(self):
        self.drop = DropComponents()

    def setup_method(self, cls):
        self.setup()

    def test_drop_package(self):
        self.drop.drop_package('some')
        assert self.drop.drop_packages == ['some']

    def test_drop_path(self):
        self.drop.drop_path('some')
        assert self.drop.drop_files_and_directories == ['/system-root/some']

    @patch('suse_migration_services.drop_components.Zypper.run')
    def test_drop_perform_package(
        self, mock_Zypper_run
    ):
        self.drop.drop_package('some')
        self.drop.drop_package('some_other')
        self.drop.drop_perform()
        mock_Zypper_run.assert_called_once_with(
            [
                '--no-cd',
                '--non-interactive',
                '--gpg-auto-import-keys',
                '--root', '/system-root',
                'remove',
                '--clean-deps',
                'some',
                'some_other'
            ], raise_on_error=False
        )

    @patch('os.path.isdir')
    @patch('shutil.rmtree')
    def test_drop_perform_directory(
        self, mock_shutil_rmtree, mock_os_path_isdir,
    ):
        mock_os_path_isdir.return_value = True
        self.drop.drop_path('some/directory')
        self.drop.drop_perform()
        mock_shutil_rmtree.assert_called_once_with(
            '/system-root/some/directory'
        )

    @patch('os.path.isdir')
    @patch('pathlib.Path')
    def test_drop_perform_file(
        self, mock_pathlib_Path, mock_os_path_isdir
    ):
        path = Mock()
        mock_pathlib_Path.return_value = path
        mock_os_path_isdir.return_value = False
        self.drop.drop_path('some/file')
        self.drop.drop_perform()
        mock_pathlib_Path.assert_called_once_with(
            '/system-root/some/file'
        )
        path.unlink.assert_called_once_with(missing_ok=True)
