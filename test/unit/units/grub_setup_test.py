from unittest.mock import (
    patch, call
)
from pytest import raises

from suse_migration_services.units.grub_setup import main
from suse_migration_services.exceptions import (
    DistMigrationGrubConfigException
)


class TestGrubSetup(object):
    @patch('suse_migration_services.logger.log.error')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    def test_main_raises_on_grub_update(
        self, mock_Command_run,
        mock_info, mock_error
    ):
        mock_Command_run.side_effect = [
            None,
            Exception,
        ]
        with raises(DistMigrationGrubConfigException):
            main()
            assert mock_info.called
            assert mock_error.called

    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    def test_main(
        self, mock_Command_run, mock_info
    ):
        main()
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'chroot', '/system-root',
                    'zypper', '--non-interactive', '--no-gpg-checks',
                    'remove', 'SLE*-Migration'
                ], raise_on_error=False
            ),
            call(
                [
                    'chroot', '/system-root',
                    'grub2-mkconfig', '-o', '/boot/grub2/grub.cfg'
                ]
            )
        ]
        assert mock_info.called
