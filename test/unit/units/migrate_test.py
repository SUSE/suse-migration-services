from unittest.mock import patch
from pytest import raises

from suse_migration_services.units.migrate import main
from suse_migration_services.defaults import Defaults
from suse_migration_services.exceptions import (
    DistMigrationZypperException
)


class TestMigration(object):
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.logger.log.error')
    @patch('suse_migration_services.command.Command.run')
    def test_main_raises_on_zypper_migration(
        self, mock_Command_run, mock_error, mock_info
    ):
        mock_Command_run.side_effect = Exception
        with raises(DistMigrationZypperException):
            main()
            assert mock_info.called
            assert mock_error.called

    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    @patch.object(Defaults, 'get_migration_config_file')
    def test_main(
        self, mock_get_migration_config_file,
        mock_Command_run, mock_info
    ):
        mock_get_migration_config_file.return_value = \
            '../data/migration-config.yml'
        main()
        mock_Command_run.assert_called_once_with(
            [
                'zypper', 'migration',
                '--non-interactive',
                '--gpg-auto-import-keys',
                '--no-selfupdate',
                '--auto-agree-with-licenses',
                '--product', 'foo',
                '--root', '/system-root'
            ]
        )
        assert mock_info.called
