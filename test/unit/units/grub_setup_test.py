from unittest.mock import patch, call
from pytest import raises

from suse_migration_services.units.grub_setup import main
from suse_migration_services.exceptions import DistMigrationGrubConfigException


@patch('suse_migration_services.logger.Logger.setup')
@patch('suse_migration_services.command.Command.run')
class TestGrubSetup(object):
    def test_main_raises_on_grub_update(self, mock_Command_run, mock_logger_setup):
        mock_Command_run.side_effect = [
            None,
            Exception,
        ]
        with raises(DistMigrationGrubConfigException):
            main()

    def test_main(self, mock_Command_run, mock_logger_setup):
        main()
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'chroot',
                    '/system-root',
                    'zypper',
                    '--non-interactive',
                    '--no-gpg-checks',
                    'remove',
                    'SLE*Migration',
                    'suse-migration-*-activation',
                ],
                raise_on_error=False,
            ),
            call(['chroot', '/system-root', 'grub2-mkconfig', '-o', '/boot/grub2/grub.cfg']),
        ]
