""" Tests for regenerate_initrd"""
import logging

from unittest.mock import (
    patch, call
)
from pytest import (
    raises, fixture
)
from suse_migration_services.defaults import Defaults
from suse_migration_services.units.regenerate_initrd import (
    main, RegenerateBootImage
)
from suse_migration_services.exceptions import (
    DistMigrationCommandException
)


class TestRegenInitrd:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        """Setup capture log"""
        self._caplog = caplog

    @patch('suse_migration_services.logger.Logger.setup')
    def setup(self, mock_Logger_setup):
        self.dracut = RegenerateBootImage()
        self.dracut.root_path = '/system-root'

    @patch('suse_migration_services.logger.Logger.setup')
    def setup_method(self, cls, mock_Logger_setup):
        self.setup()

    @patch('suse_migration_services.logger.Logger.setup')
    @patch('os.path.exists')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.command.Command.run')
    def test_main_raises_on_regenerate_initrd(
        self, mock_Command_run, mock_get_migration_config_file,
        mock_os_path_exists, mock_logger_setup
    ):
        mock_get_migration_config_file.return_value = \
            '../data/migration-config-initrd.yml'
        mock_Command_run.side_effect = [
            None,
            None,
            None,
            Exception('error')
        ]
        with self._caplog.at_level(logging.ERROR):
            with raises(DistMigrationCommandException):
                main()

    @patch('suse_migration_services.logger.Logger.setup')
    @patch('os.path.exists')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.command.Command.run')
    def test_main_initrd_skipped_because_handled_at_install_time(
        self, mock_Command_run, mock_get_migration_config_file,
        mock_os_path_exists, mock_logger_setup
    ):
        with self._caplog.at_level(logging.INFO):
            main()
            assert 'No action needed' in self._caplog.text

    @patch('suse_migration_services.logger.Logger.setup')
    @patch('os.path.exists')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.command.Command.run')
    def test_dracut_bind_mounts_raises_on_regen_initrd(
        self, mock_Command_run, mock_get_migration_config_file,
        mock_os_path_exists, mock_logger_setup
    ):
        mock_get_migration_config_file.return_value = \
            '../data/migration-config-initrd.yml'
        mock_Command_run.side_effect = [
            Exception('error'),
            Exception('error'),
            Exception('error')
        ]
        with self._caplog.at_level(logging.ERROR):
            with raises(DistMigrationCommandException):
                self.dracut._dracut_bind_mounts()

    @patch('suse_migration_services.logger.Logger.setup')
    @patch('os.path.exists')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.command.Command.run')
    def test_main(
        self, mock_Command_run, mock_get_migration_config_file,
        mock_os_path_exists, mock_logger_setup
    ):
        mock_get_migration_config_file.return_value = \
            '../data/migration-config-initrd.yml'
        main()
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'mount',
                    '--bind',
                    '/dev',
                    '/system-root/dev',
                ]
            ),
            call(
                [
                    'mount',
                    '--bind',
                    '/proc',
                    '/system-root/proc',
                ]
            ),
            call(
                [
                    'mount',
                    '--bind',
                    '/sys',
                    '/system-root/sys',
                ]
            ),
            call(
                [
                    'bash', '-c', 'chroot /system-root '
                    'dracut --force --verbose --no-host-only '
                    '--no-hostonly-cmdline --regenerate-all &>> '
                    '/var/log/distro_migration.log'
                ]
            )
        ]
