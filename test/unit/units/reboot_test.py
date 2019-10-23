from unittest.mock import (
    patch, call, MagicMock, Mock
)
from suse_migration_services.units.reboot import main
from suse_migration_services.fstab import Fstab
from suse_migration_services.defaults import Defaults


class TestKernelReboot(object):
    @patch('suse_migration_services.logger.log.warning')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.reboot.MigrationConfig')
    def test_main_skip_reboot_due_to_debug_file_set(
        self, mock_MigrationConfig, mock_Command_run, mock_info,
        mock_warning
    ):
        config = Mock()
        config.is_debug_requested.return_value = True
        mock_MigrationConfig.return_value = config
        main()
        assert mock_info.call_args_list[1] == call(
            'Reboot skipped due to debug flag set'
        )

    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.reboot.Fstab')
    def test_main_kexec_reboot(
        self, mock_Fstab, mock_Command_run,
        mock_info, mock_get_migration_config_file
    ):
        fstab = Fstab()
        fstab_mock = Mock()
        fstab_mock.read.return_value = fstab.read('../data/system-root.fstab')
        fstab_mock.get_devices.return_value = fstab.get_devices()
        mock_Fstab.return_value = fstab_mock
        mock_get_migration_config_file.return_value = \
            '../data/migration-config.yml'
        main()
        assert mock_info.called
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
            call(['systemctl', 'reboot'])
        ]

    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.logger.log.warning')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.reboot.Fstab')
    def test_main_force_reboot(
        self, mock_Fstab, mock_Command_run, mock_info,
        mock_warning, mock_get_migration_config_file
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
            '../data/migration-config.yml'
        main()
        assert mock_info.called
        assert mock_Command_run.call_args_list == [
            call(['systemctl', 'status', '-l', '--all'], raise_on_error=False),
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
        mock_warning.assert_called_once_with(
            'Reboot system: [Force Reboot]'
        )
