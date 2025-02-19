""" Tests for update_bootloader"""
import logging

from unittest.mock import (
    patch, call
)
from pytest import (
    raises, fixture
)
from suse_migration_services.units.update_bootloader import (
    main,
    install_shim_package,
    install_secure_bootloader,
    update_bootloader_config
)
from suse_migration_services.exceptions import (
    DistMigrationCommandException
)


@patch('suse_migration_services.logger.Logger.setup')
@patch('os.path.exists')
class TestUpdateBootloader():
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        """Setup capture log"""
        self._caplog = caplog

    @patch('suse_migration_services.command.Command.run')
    def test_install_shim_package_raises(
        self,
        mock_Command_run,
        mock_os_path_exists,
        mock_logger_setup
    ):
        """ Test exception raised when running update_bootloader"""

        mock_Command_run.side_effect = [
            Exception('error')
        ]
        with self._caplog.at_level(logging.ERROR):
            with raises(DistMigrationCommandException):
                install_shim_package('/system-root')
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'chroot',
                    '/system-root',
                    'zypper',
                    'in',
                    'shim'
                ]
            )
        ]

    @patch('suse_migration_services.command.Command.run')
    def test_install_secure_bootloader_raises_on_update_bootloader(
        self,
        mock_Command_run,
        mock_os_path_exists,
        mock_logger_setup
    ):
        """ Test exception raised when running dracut_bind_mounts()"""
        mock_Command_run.side_effect = [
            Exception('error')
        ]
        with self._caplog.at_level(logging.ERROR):
            with raises(DistMigrationCommandException):
                install_secure_bootloader('/system-root')

    @patch('suse_migration_services.command.Command.run')
    def test_update_bootloader_config_raise_on_update_bootloader(
        self,
        mock_Command_run,
        mock_os_path_exists,
        mock_logger_setup
    ):
        """ Test exception raised when running dracut_bind_mounts()"""
        mock_Command_run.side_effect = [
            Exception('error')
        ]
        with self._caplog.at_level(logging.ERROR):
            with raises(DistMigrationCommandException):
                update_bootloader_config('/system-root')

    @patch('suse_migration_services.command.Command.run')
    def test_main(
        self,
        mock_Command_run,
        mock_os_path_exists,
        mock_logger_setup
    ):
        """ Test running update_bootloader"""
        main()
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'chroot',
                    '/system-root',
                    'zypper',
                    'in',
                    'shim'
                ]
            ),
            call(
                [
                    'chroot',
                    '/system-root',
                    'shim-install',
                    '--removable'
                ]
            ),
            call(
                [
                    'chroot',
                    '/system-root',
                    'update-bootloader',
                    '--reinit'
                ]
            )
        ]
