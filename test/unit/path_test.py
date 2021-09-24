from unittest.mock import patch
import os

from suse_migration_services.path import Path


@patch('suse_migration_services.command.Command.run')
class TestPath(object):
    def test_create(self, mock_command):
        Path.create('foo')
        mock_command.assert_called_once_with(
            ['mkdir', '-p', 'foo']
        )

    def test_wipe(self, mock_command):
        Path.wipe('foo')
        mock_command.assert_called_once_with(
            ['rm', '-r', '-f', 'foo']
        )

    def test_remove(self, mock_command):
        Path.remove('foo')
        mock_command.assert_called_once_with(
            ['rmdir', 'foo']
        )

    @patch('os.access')
    @patch('os.environ.get')
    @patch('os.path.exists')
    def test_which(self, mock_exists, mock_env, mock_access, mock_Command):
        mock_env.return_value = '/usr/local/bin:/usr/bin:/bin'
        mock_exists.return_value = True
        assert Path.which('some-file') == '/usr/local/bin/some-file'
        mock_exists.return_value = False
        assert Path.which('some-file') is None
        mock_env.return_value = None
        mock_exists.return_value = True
        assert Path.which('some-file', ['alternative']) == \
            'alternative/some-file'
        mock_access.return_value = False
        mock_env.return_value = '/usr/local/bin:/usr/bin:/bin'
        assert Path.which('some-file', access_mode=os.X_OK) is None
        mock_access.return_value = True
        assert Path.which('some-file', access_mode=os.X_OK) == \
            '/usr/local/bin/some-file'
        assert Path.which('some-file', custom_env={'PATH': 'custom_path'}) == \
            'custom_path/some-file'

    @patch('os.access')
    @patch('os.environ.get')
    @patch('os.path.exists')
    def test_which_not_found(
        self, mock_exists, mock_env, mock_access, mock_Command
    ):
        mock_env.return_value = '/usr/local/bin:/usr/bin:/bin'
        mock_exists.return_value = False
        assert Path.which('file') is None

    @patch('os.access')
    @patch('os.environ.get')
    @patch('os.path.exists')
    def test_which_not_found_for_mode(
        self, mock_exists, mock_env, mock_access, mock_Command
    ):
        mock_env.return_value = '/usr/local/bin:/usr/bin:/bin'
        mock_exists.return_value = True
        mock_access.return_value = False
        assert Path.which('file', access_mode=os.X_OK) is None
