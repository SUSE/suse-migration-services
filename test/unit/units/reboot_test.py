import logging
from unittest.mock import (
    patch, call, MagicMock, Mock
)
from pytest import fixture
from suse_migration_services.units.reboot import main
from suse_migration_services.fstab import Fstab
from suse_migration_services.defaults import Defaults


class TestKernelReboot(object):
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.reboot.MigrationConfig')
    def test_main_skip_reboot_due_to_debug_file_set(
        self, mock_MigrationConfig, mock_Command_run, mock_logger_setup
    ):
        config = Mock()
        config.is_debug_requested.return_value = True
        mock_MigrationConfig.return_value = config
        with self._caplog.at_level(logging.INFO):
            main()
            assert 'Reboot skipped due to debug flag set' in self._caplog.text

    @patch('suse_migration_services.fstab.Fstab._is_on_root')
    @patch('suse_migration_services.fstab.Fstab._get_root_disk')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.reboot.Fstab')
    def test_main_kexec_reboot(
        self, mock_Fstab, mock_Command_run,
        mock_logger_setup, mock_get_migration_config_file,
        mock_get_root_disk, mock_is_on_root
    ):
        fstab = Fstab()
        fstab_mock = Mock()
        fstab_mock.read.return_value = fstab.read('../data/system-root.fstab')
        fstab_mock.get_devices.return_value = fstab.get_devices()
        mock_Fstab.return_value = fstab_mock
        mock_get_migration_config_file.return_value = \
            '../data/migration-config.yml'
        mock_get_root_disk.return_value = 'sda3 /'
        mock_is_on_root.return_value = True
        main()
        assert mock_Command_run.call_args_list == [
            call(
                ['systemctl', 'status', '-l', '--all'],
                raise_on_error=False
            ),
            call(
                ['umount', '--lazy', '/system-root/home'],
                raise_on_error=False
            ),
            call(
                ['umount', '--lazy', '/system-root/boot/efi'],
                raise_on_error=False
            ),
            call(
                ['umount', '--lazy', '/system-root/'],
                raise_on_error=False
            ),
            call(['systemctl', 'kexec'])
        ]

    @patch('suse_migration_services.fstab.Fstab._is_on_root')
    @patch('suse_migration_services.fstab.Fstab._get_root_disk')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.reboot.Fstab')
    def test_main_force_reboot(
        self, mock_Fstab, mock_Command_run, mock_logger_setup,
        mock_get_migration_config_file, mock_get_root_disk, mock_is_on_root
    ):
        fstab = Fstab()
        fstab_mock = Mock()
        fstab_mock.read.return_value = fstab.read('../data/system-root.fstab')
        fstab_mock.get_devices.return_value = fstab.get_devices()
        mock_Fstab.return_value = fstab_mock
        mock_Command_run.side_effect = [
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            Exception,
            None
        ]
        mock_get_migration_config_file.return_value = \
            '../data/migration-config-hard-reboot.yml'
        mock_get_root_disk.return_value = 'sda3 /'
        mock_is_on_root.return_value = True
        with self._caplog.at_level(logging.WARNING):
            main()
            assert mock_Command_run.call_args_list == [
                call(
                    ['systemctl', 'status', '-l', '--all'],
                    raise_on_error=False
                ),
                call(
                    ['umount', '--lazy', '/system-root/home'],
                    raise_on_error=False
                ),
                call(
                    ['umount', '--lazy', '/system-root/boot/efi'],
                    raise_on_error=False
                ),
                call(
                    ['umount', '--lazy', '/system-root/'],
                    raise_on_error=False
                ),
                call(['systemctl', 'reboot']),
                call(['systemctl', '--force', 'reboot'])
            ]
            assert 'Reboot system: [Force Reboot]' in self._caplog.text
