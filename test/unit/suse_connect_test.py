import logging
from pytest import fixture
from unittest.mock import (
    patch, Mock
)

# project
from suse_migration_services.suse_connect import SUSEConnect


@patch('suse_migration_services.command.Command.run')
class TestSUSEConnect(object):
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def test_is_registered(
        self, mock_Command_run
    ):
        command = Mock()
        command.returncode = 0
        mock_Command_run.return_value = command
        assert SUSEConnect().is_registered() is True
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
        with self._caplog.at_level(logging.ERROR):
            assert SUSEConnect().is_registered() is False
            mock_Command_run.assert_called_once_with(
                [
                    'chroot', '/system-root', 'SUSEConnect',
                    '--list-extensions'
                ], raise_on_error=False
            )
            assert 'it is not registered' in self._caplog.text
