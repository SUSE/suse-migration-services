import logging
from unittest.mock import (
    patch, call, MagicMock, Mock
)
from pytest import fixture
from suse_migration_services.units.reboot import main
from suse_migration_services.fstab import Fstab
from suse_migration_services.defaults import Defaults


@patch('suse_migration_services.command.Command.run')
@patch('suse_migration_services.logger.Logger.setup')
@patch.object(Defaults, 'get_migration_config_file')
class TestKernelReboot(object):
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('suse_migration_services.units.reboot.MigrationConfig')
    def test_main_skip_reboot_due_to_debug_file_set(
        self, mock_MigrationConfig, mock_config_file,
        mock_logger_setup, mock_Command_run
    ):
        config = Mock()
        config.is_debug_requested.return_value = True
        mock_MigrationConfig.return_value = config
        with self._caplog.at_level(logging.INFO):
            main()
            assert 'Reboot skipped due to debug flag set' in self._caplog.text

    @patch('os.path.exists')
    @patch('suse_migration_services.units.reboot.Fstab')
    def test_main_kexec_reboot(
        self, mock_Fstab, mock_os_path_exists,
        mock_get_migration_config_file, mock_logger_setup,
        mock_Command_run,
    ):
        def skip_device(device):
            if '/dev/mynode' in device:
                return False
            return True

        mock_os_path_exists.side_effect = skip_device
        fstab = Fstab()
        fstab_mock = Mock()
        fstab_mock.read.return_value = fstab.read('../data/system-root.fstab')
        fstab_mock.get_devices.return_value = fstab.get_devices()
        mock_Fstab.return_value = fstab_mock
        mock_get_migration_config_file.return_value = \
            '../data/migration-config.yml'
        main()
        assert mock_Command_run.call_args_list == [
            call(
                ['systemctl', 'status', '-l', '--all'],
                raise_on_error=False
            ),
            call(
                ['systemctl', 'stop', 'suse-migration-console-log'],
                raise_on_error=False
            ),
            call(
                ['umount', '--lazy', '/system-root/boot/efi'],
                raise_on_error=False
            ),
            call(
                ['umount', '--lazy', '/system-root/home'],
                raise_on_error=False
            ),
            call(
                ['umount', '--lazy', '/system-root/'],
                raise_on_error=False
            ),
            call(['systemctl', 'kexec'])
        ]

    @patch('os.path.exists')
    @patch('suse_migration_services.units.reboot.Fstab')
    def test_main_force_reboot(
        self, mock_Fstab, mock_os_path_exists,
        mock_get_migration_config_file, mock_logger_setup,
        mock_Command_run,
    ):
        def skip_device(device):
            if '/dev/mynode' in device:
                return False
            return True

        mock_os_path_exists.side_effect = skip_device
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
            MagicMock(),
            Exception,
            None
        ]
        mock_get_migration_config_file.return_value = \
            '../data/migration-config-hard-reboot.yml'
        with self._caplog.at_level(logging.WARNING):
            main()
            assert mock_Command_run.call_args_list == [
                call(
                    ['systemctl', 'status', '-l', '--all'],
                    raise_on_error=False
                ),
                call(
                    ['systemctl', 'stop', 'suse-migration-console-log'],
                    raise_on_error=False
                ),
                call(
                    ['umount', '--lazy', '/system-root/boot/efi'],
                    raise_on_error=False
                ),
                call(
                    ['umount', '--lazy', '/system-root/home'],
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
