import os
from unittest.mock import patch
from pytest import raises

from suse_migration_services.units.migrate import main
from suse_migration_services.defaults import Defaults
from suse_migration_services.exceptions import (
    DistMigrationZypperException
)


class TestMigration(object):
    @patch('shutil.copy')
    @patch('os.path.exists')
    @patch('suse_migration_services.defaults.Defaults.get_system_root_path')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.logger.log.error')
    @patch('suse_migration_services.command.Command.run')
    def test_main_raises_on_zypper_migration(
        self, mock_Command_run, mock_error, mock_info,
        mock_get_system_root_path, mock_path_exists, mock_shutil_copy
    ):
        mock_Command_run.side_effect = Exception
        mock_get_system_root_path.return_value = '../data'
        mock_path_exists.return_value = True
        with raises(DistMigrationZypperException):
            main()
        issue_path = '../data/etc/issue'
        with open(issue_path) as issue_file:
            message = (
                'Migration has failed, for further details see {0}'
                .format('/var/log/distro_migration.log')
            )
            assert message in issue_file.read()
        os.remove(issue_path)
        mock_shutil_copy.assert_called_once_with(
            '../data/etc/sle-migration-service',
            '/etc/sle-migration-service'
        )
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
                'bash', '-c',
                'zypper migration '
                '--non-interactive '
                '--gpg-auto-import-keys '
                '--no-selfupdate '
                '--auto-agree-with-licenses '
                '--strict-errors-dist-migration '
                '--product foo '
                '--root /system-root '
                '&>> /system-root/var/log/distro_migration.log'
            ]
        )
        assert mock_info.called
