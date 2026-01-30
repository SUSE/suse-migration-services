import os

from unittest.mock import patch, Mock
from pytest import raises
from collections import namedtuple

from suse_migration_services.command import Command

from suse_migration_services.exceptions import (
    DistMigrationCommandException,
    DistMigrationCommandNotFoundException,
)


@patch('suse_migration_services.path.Path.which')
class TestCommand(object):
    @patch('subprocess.Popen')
    def test_run_raises_error(self, mock_popen, mock_which):
        mock_which.return_value = 'command'
        mock_process = Mock()
        mock_process.communicate = Mock(return_value=[str.encode('stdout'), str.encode('stderr')])
        mock_process.returncode = 1
        mock_popen.return_value = mock_process
        with raises(DistMigrationCommandException):
            Command.run(['command', 'args'])

    @patch('subprocess.Popen')
    def test_run_failure(self, mock_popen, mock_which):
        mock_which.return_value = 'command'
        mock_popen.side_effect = DistMigrationCommandException('Run failure')
        with raises(DistMigrationCommandException):
            Command.run(['command', 'args'])

    def test_run_invalid_environment(self, mock_which):
        mock_which.return_value = False
        with raises(DistMigrationCommandNotFoundException):
            Command.run(['command', 'args'], {'HOME': '/root'})

    @patch('subprocess.Popen')
    def test_run_does_not_raise_error(self, mock_popen, mock_which):
        mock_which.return_value = 'command'
        mock_process = Mock()
        mock_process.communicate = Mock(return_value=[str.encode('stdout'), str.encode('')])
        mock_process.returncode = 1
        mock_popen.return_value = mock_process
        result = Command.run(['command', 'args'], os.environ, False)
        assert result.error == '(no output on stderr)'
        assert result.output == 'stdout'
        mock_process.communicate = Mock(return_value=[str.encode(''), str.encode('stderr')])
        result = Command.run(['command', 'args'], os.environ, False)
        assert result.error == 'stderr'
        assert result.output == '(no output on stdout)'

    def test_run_does_not_raise_error_if_command_not_found(self, mock_which):
        mock_which.return_value = None
        result = Command.run(['command', 'args'], os.environ, False)
        assert result.error is None
        assert result.output is None
        assert result.returncode == -1

    @patch('os.access')
    @patch('os.path.exists')
    @patch('subprocess.Popen')
    def test_run(self, mock_popen, mock_exists, mock_access, mock_which):
        mock_exists.return_value = True
        command_run = namedtuple('command', ['output', 'error', 'returncode'])
        run_result = command_run(output='stdout', error='stderr', returncode=0)
        mock_process = Mock()
        mock_process.communicate = Mock(return_value=[str.encode('stdout'), str.encode('stderr')])
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        mock_access.return_value = True
        assert Command.run(['command', 'args']) == run_result
