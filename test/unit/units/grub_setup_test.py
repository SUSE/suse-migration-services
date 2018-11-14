from unittest.mock import (
    patch, call
)
from pytest import raises

from suse_migration_services.units.grub_setup import main
from suse_migration_services.exceptions import (
    DistMigrationGrubException
)


class TestSetupHostNetwork(object):
    @patch('suse_migration_services.command.Command.run')
    def test_main_raises_on_grub_update(
        self, mock_Command_run
    ):
        mock_Command_run.side_effect = Exception
        with raises(DistMigrationGrubException):
            main()

    @patch('suse_migration_services.command.Command.run')
    def test_main(
        self, mock_Command_run
    ):
        main()
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'mount', '--bind', '/dev',
                    '/system-root/dev'
                ]
            ),
            call(
                [
                    'mount', '--bind', '/proc',
                    '/system-root/proc'
                ]
            ),
            call(
                ['chroot', '/system-root']
            ),
            call(
                ['grub2-mkconfig', '-o', '/boot/grub2/grub.cfg']
            )
        ]
