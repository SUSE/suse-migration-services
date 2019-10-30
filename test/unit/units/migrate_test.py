import io
from unittest.mock import (
    patch, Mock, MagicMock
)
from pytest import raises

from suse_migration_services.units.migrate import main
from suse_migration_services.defaults import Defaults
from suse_migration_services.migration_config import MigrationConfig
from suse_migration_services.exceptions import (
    DistMigrationZypperException
)


class TestMigration(object):
    @patch('suse_migration_services.defaults.Defaults.get_system_root_path')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.migrate.MigrationConfig')
    @patch('suse_migration_services.logger.log.error')
    @patch('suse_migration_services.logger.log.info')
    def test_main_zypper_migration_plugin_raises(
        self, mock_info, mock_error, mock_MigrationConfig, mock_Command_run,
        mock_get_system_root_path
    ):
        migration_config = Mock()
        migration_config.get_migration_product.return_value = 'product'
        migration_config.is_zypper_migration_plugin_requested.return_value = \
            True
        mock_MigrationConfig.return_value = migration_config
        mock_Command_run.side_effect = Exception
        mock_get_system_root_path.return_value = '../data'
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            with raises(DistMigrationZypperException):
                main()
            mock_open.assert_called_once_with(
                '../data/etc/issue', 'w'
            )
            file_handle.write.assert_called_once_with(
                'Migration has failed, for further details see {0}'.format(
                    '/var/log/distro_migration.log'
                )
            )

    @patch('suse_migration_services.defaults.Defaults.get_system_root_path')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.migrate.MigrationConfig')
    @patch('suse_migration_services.logger.log.error')
    @patch('suse_migration_services.logger.log.info')
    def test_main_zypper_dup_raises(
        self, mock_info, mock_error, mock_MigrationConfig, mock_Command_run,
        mock_get_system_root_path
    ):
        migration_config = Mock()
        migration_config.is_zypper_migration_plugin_requested.return_value = \
            False
        mock_MigrationConfig.return_value = migration_config
        zypper_call = Mock()
        zypper_call.returncode = 0
        mock_Command_run.return_value = zypper_call
        mock_get_system_root_path.return_value = '../data'
        with patch('builtins.open', create=True):
            # zypper exit code is 0, all ok
            main()
            # zypper exit code is 1, error
            zypper_call.returncode = 1
            with raises(DistMigrationZypperException):
                main()
            # zypper exit code is 104, error
            zypper_call.returncode = 104
            with raises(DistMigrationZypperException):
                main()
            # zypper exit code is 105, error
            zypper_call.returncode = 105
            with raises(DistMigrationZypperException):
                main()
            # zypper exit code is 106, error
            zypper_call.returncode = 106
            with raises(DistMigrationZypperException):
                main()
            # zypper exit code is 107, all ok
            zypper_call.returncode = 107
            main()

    @patch.object(MigrationConfig, 'get_migration_product')
    @patch('suse_migration_services.command.Command.run')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.logger.log.error')
    @patch('suse_migration_services.logger.log.info')
    def test_main_zypper_migration_plugin(
        self, mock_info, mock_error, mock_get_migration_config_file,
        mock_Command_run, mock_get_system_root_path
    ):
        mock_get_system_root_path.return_value = 'SLES/15/x86_64'
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
                '--allow-vendor-change '
                '--strict-errors-dist-migration '
                '--replacefiles '
                '--product SLES/15/x86_64 '
                '--root /system-root '
                '&>> /system-root/var/log/distro_migration.log'
            ]
        )

    @patch('suse_migration_services.command.Command.run')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.logger.log.error')
    @patch('suse_migration_services.logger.log.info')
    def test_main_zypper_dup(
        self, mock_info, mock_error, mock_get_migration_config_file,
        mock_Command_run
    ):
        zypper_call = Mock()
        zypper_call.returncode = 0
        mock_Command_run.return_value = zypper_call
        mock_get_migration_config_file.return_value = \
            '../data/migration-config-zypper-dup.yml'
        main()
        mock_Command_run.assert_called_once_with(
            [
                'bash', '-c',
                'zypper --non-interactive '
                '--gpg-auto-import-keys '
                '--root /system-root '
                'dup '
                '--auto-agree-with-licenses '
                '--allow-vendor-change '
                '--replacefiles '
                '&>> /system-root/var/log/distro_migration.log'
            ], raise_on_error=False
        )
