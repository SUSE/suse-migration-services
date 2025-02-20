from pytest import raises
from unittest.mock import (
    patch, call
)

from suse_migration_services.units.wicked_migration import main
from suse_migration_services.exceptions import (
    DistMigrationWickedMigrationException
)


@patch('suse_migration_services.logger.Logger.setup')
class TestMigrationWicked(object):
    @patch('suse_migration_services.command.Command.run')
    def test_main(self, mock_Command_run, mock_logger_setup):
        main()
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'systemctl', '--root', '/system-root',
                    'enable', '--force', 'NetworkManager.service'
                ]
            ),
            call(
                [
                    'systemctl', '--root', '/system-root',
                    'mask', 'wicked.service'
                ]
            )
        ]

    @patch('suse_migration_services.command.Command.run')
    def test_main_raises(self, mock_Command_run, mock_logger_setup):
        mock_Command_run.side_effect = Exception
        with raises(DistMigrationWickedMigrationException):
            main()
