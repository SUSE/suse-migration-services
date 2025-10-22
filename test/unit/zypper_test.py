from unittest.mock import patch
from pytest import raises
from collections import namedtuple

from suse_migration_services.zypper import Zypper, ZypperCall

from suse_migration_services.exceptions import (
    DistMigrationZypperException
)


@patch('suse_migration_services.command.Command.run')
class TestCommand(object):
    def test_zypper_run(self, mock_Command_run):
        command_run_result = namedtuple(
            'command', ['output', 'error', 'returncode']
        )
        mock_Command_run.return_value = command_run_result(
            output='', error='', returncode=0
        )
        Zypper.run(['in', 'test', '--root', '/system-root'])
        mock_Command_run.assert_called_once_with(
            [
                'bash', '-c',
                'zypper in test --root /system-root '
                '&>> /system-root/var/log/distro_migration.log'
            ], raise_on_error=True
        )

    def test_zypper_run_chroot(self, mock_Command_run):
        command_run_result = namedtuple(
            'command', ['output', 'error', 'returncode']
        )
        mock_Command_run.return_value = command_run_result(
            output='', error='', returncode=0
        )
        Zypper.run(['in', 'test', '--root', '/system-root'], chroot='root')
        mock_Command_run.assert_called_once_with(
            [
                'chroot', 'root', 'bash', '-c',
                'zypper in test --root /system-root '
                '&>> /var/log/distro_migration.log'
            ], raise_on_error=True
        )

    def test_zypper_raises(self, mock_Command_run):
        mock_Command_run.side_effect = Exception
        with raises(DistMigrationZypperException):
            Zypper.run([])

    def test_zypper_dont_raise_on_error(self, mock_Command_run):
        command_run_result = namedtuple(
            'command', ['output', 'error', 'returncode']
        )
        mock_Command_run.return_value = command_run_result(
            output='', error='', returncode=1
        )
        zypper_call = Zypper.run(['in', 'test', '--root', '/system-root'], raise_on_error=False)
        mock_Command_run.assert_called_once_with(
            [
                'bash', '-c',
                'zypper in test --root /system-root '
                '&>> /system-root/var/log/distro_migration.log'
            ], raise_on_error=False
        )

        assert not zypper_call.success
        with raises(DistMigrationZypperException):
            zypper_call.raise_if_failed()

    def test_zypper_call_failed(self, mock_Command_run):
        command_run_result = namedtuple(
            'command', ['output', 'error', 'returncode']
        )

        # zypper exit code is 0, all ok
        result = command_run_result(
            output='', error='', returncode=0
        )
        zypper_call = ZypperCall([], '', result)
        assert zypper_call.success
        zypper_call.raise_if_failed()

        # zypper exit code is 1, error
        result = command_run_result(
            output='', error='', returncode=1
        )
        zypper_call = ZypperCall([], '', result)
        assert not zypper_call.success
        with raises(DistMigrationZypperException):
            zypper_call.raise_if_failed()

        # zypper exit code is 104, error
        result = command_run_result(
            output='', error='', returncode=104
        )
        zypper_call = ZypperCall([], '', result)
        assert not zypper_call.success
        with raises(DistMigrationZypperException):
            zypper_call.raise_if_failed()

        # zypper exit code is 105, error
        result = command_run_result(
            output='', error='', returncode=105
        )
        zypper_call = ZypperCall([], '', result)
        assert not zypper_call.success
        with raises(DistMigrationZypperException):
            zypper_call.raise_if_failed()

        # zypper exit code is 106, error
        result = command_run_result(
            output='', error='', returncode=106
        )
        zypper_call = ZypperCall([], '', result)
        assert not zypper_call.success
        with raises(DistMigrationZypperException):
            zypper_call.raise_if_failed()

        # zypper exit code is 107, ok
        result = command_run_result(
            output='', error='', returncode=107
        )
        zypper_call = ZypperCall([], '', result)
        assert zypper_call.success
        zypper_call.raise_if_failed()
