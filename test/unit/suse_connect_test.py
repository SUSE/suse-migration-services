from unittest.mock import (
    patch, Mock
)

# project
from suse_migration_services.suse_connect import SUSEConnect


@patch('suse_migration_services.command.Command.run')
class TestSUSEConnect(object):
    def test_is_registered(
        self, mock_Command_run
    ):
        command = Mock()
        command.returncode = 0
        mock_Command_run.return_value = command
        assert SUSEConnect().is_registered(Mock()) is True
        mock_Command_run.assert_called_once_with(
            [
                'chroot', '/system-root', 'SUSEConnect',
                '--list-extensions'
            ], raise_on_error=False
        )

    def test_is_not_registered(self, mock_Command_run):
        command = Mock()
        command.returncode = 1
        command.output = 'it is not registered'
        mock_Command_run.return_value = command
        log = Mock()
        assert SUSEConnect().is_registered(log) is False
        mock_Command_run.assert_called_once_with(
            [
                'chroot', '/system-root', 'SUSEConnect',
                '--list-extensions'
            ], raise_on_error=False
        )
        log.error.assert_called_once_with('it is not registered')
