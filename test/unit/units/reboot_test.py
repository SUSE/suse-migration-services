from unittest.mock import (
    patch, call, MagicMock, Mock
)
from suse_migration_services.units.reboot import main
from suse_migration_services.fstab import Fstab


class TestKernelReboot(object):
    @patch('os.path.exists')
    @patch('suse_migration_services.logger.log.warning')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    def test_main_skip_reboot_due_to_debug_file_set(
        self, mock_Command_run, mock_info, mock_warning, mock_path_exists
    ):
        mock_path_exists.return_value = True
        main()
        assert mock_info.called

    @patch('os.path.exists')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.reboot.Fstab')
    def test_main_kexec_reboot(
        self, mock_Fstab, mock_Command_run, mock_info, mock_path_exists
    ):
        fstab = Fstab()
        fstab_mock = Mock()
        fstab_mock.read.return_value = fstab.read('../data/system-root.fstab')
        fstab_mock.get_devices.return_value = fstab.get_devices()
        mock_Fstab.return_value = fstab_mock
        mock_path_exists.return_value = False
        main()
        mock_path_exists.assert_called_once_with(
            '/etc/sle-migration-service'
        )
        assert mock_info.called
        assert mock_Command_run.call_args_list == [
            call(
                ['systemctl', 'status', '-l', '--all'],
                raise_on_error=False
            ),
            call(
                ['umount', '--lazy', '/etc/sysconfig/network'],
                raise_on_error=False
            ),
            call(
                ['umount', '--lazy', '/etc/zypp'],
                raise_on_error=False
            ),
            call(
                ['umount', '--lazy', '/system-root/foo'],
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
            call(['kexec', '--exec'])
        ]

    @patch('suse_migration_services.logger.log.warning')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.reboot.Fstab')
    def test_main_force_reboot(
        self, mock_Fstab, mock_Command_run, mock_info, mock_warning
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
            MagicMock(),
            MagicMock(),
            MagicMock(),
            Exception,
            None
        ]
        main()
        assert mock_info.called
        assert mock_Command_run.call_args_list == [
            call(['systemctl', 'status', '-l', '--all'], raise_on_error=False),
            call(
                ['umount', '--lazy', '/etc/sysconfig/network'],
                raise_on_error=False
            ),
            call(
                ['umount', '--lazy', '/etc/zypp'],
                raise_on_error=False
            ),
            call(
                ['umount', '--lazy', '/system-root/foo'],
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
            call(['kexec', '--exec']),
            call(['reboot', '-f'])
        ]
        mock_warning.assert_called_once_with(
            'Reboot system: [Force Reboot]'
        )
