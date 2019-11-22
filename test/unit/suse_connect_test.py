from unittest.mock import (
    patch, Mock
)

# project
from suse_migration_services.suse_connect import SUSEConnect


class TestSUSEConnect(object):
    @patch('suse_migration_services.command.Command.run')
    def test_is_registered(
        self, mock_Command_run
    ):
        command = Mock()
        command.returncode = 0
        mock_Command_run.return_value = command
        assert SUSEConnect().is_registered()

    @patch('suse_migration_services.logger.log.error')
    @patch('suse_migration_services.command.Command.run')
    def test_is_not_registered(
            self, mock_Command_run, mock_error
    ):
        command = Mock()
        command.returncode = 1
        command.output = 'it is not registered'
        mock_Command_run.return_value = command
        assert not SUSEConnect().is_registered()
        mock_error.assert_called_once_with('it is not registered')
