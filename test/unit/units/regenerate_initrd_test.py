""" Tests for regenerate_initrd"""
import logging

from mock import (
    patch, call
)
from pytest import (
    raises, fixture
)
from suse_migration_services.defaults import Defaults
from suse_migration_services.units.regenerate_initrd import (
    main, dracut_bind_mounts
)
from suse_migration_services.exceptions import (
    DistMigrationCommandException
)


@patch('suse_migration_services.logger.Logger.setup')
@patch('os.path.exists')
class TestRegenInitrd():
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        """Setup capture log"""
        self._caplog = caplog

    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.command.Command.run')
    def test_main_raises_on_regen_initrd(
        self, mock_Command_run, mock_get_migration_config_file,
        mock_os_path_exists, mock_logger_setup
    ):
        """ Test exception raised when running regenerate_initrd"""
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
                    'chroot',
                    '/system-root',
                    'dracut',
                    '--no-kernel',
                    '--no-host-only',
                    '--no-hostonly-cmdline',
                    '--regenerate-all',
                    '--logfile',
                    '/tmp/host_independent_initrd.log',
                    '-f'
                ]
            )
        ]

    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.command.Command.run')
    def test_dracut_bind_mounts_raises_on_regen_initrd(
        self, mock_Command_run, mock_get_migration_config_file,
        mock_os_path_exists, mock_logger_setup
    ):
        """ Test exception raised when running dracut_bind_mounts()"""
        mock_get_migration_config_file.return_value = \
            '../data/migration-config-initrd.yml'
        mock_Command_run.side_effect = [
            Exception('error'),
            Exception('error'),
            Exception('error')
        ]
        with self._caplog.at_level(logging.ERROR):
            with raises(DistMigrationCommandException):
                dracut_bind_mounts('/system-root')

    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.command.Command.run')
    def test_main(
        self, mock_Command_run, mock_get_migration_config_file,
        mock_os_path_exists, mock_logger_setup
    ):
        """ Test running regenerate_initrd"""
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
                    'chroot',
                    '/system-root',
                    'dracut',
                    '--no-kernel',
                    '--no-host-only',
                    '--no-hostonly-cmdline',
                    '--regenerate-all',
                    '--logfile',
                    '/tmp/host_independent_initrd.log',
                    '-f'
                ]
            ),
            call(
                [
                    'chroot',
                    '/system-root',
                    'cat',
                    '/tmp/host_independent_initrd.log',
                    '>> /var/log/distro_migration.log'
                ]
            ),
            call(
                [
                    'chroot',
                    '/system-root',
                    'rm',
                    '/tmp/host_independent_initrd.log'
                ]
            )
        ]
