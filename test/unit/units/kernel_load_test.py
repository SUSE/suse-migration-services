import io
import os
import logging
from mock import (
    patch, call, MagicMock
)
from pytest import (
    raises, fixture
)
from suse_migration_services.defaults import Defaults
from suse_migration_services.units.kernel_load import (
    main, _get_cmdline
)
from suse_migration_services.exceptions import (
    DistMigrationKernelRebootException
)


class TestKernelLoad(object):
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('suse_migration_services.logger.Logger.setup')
    @patch('os.path.exists')
    def test_get_cmd_line_grub_cfg_not_present(
        self, mock_os_path_exists, mock_logger_setup
    ):
        mock_os_path_exists.return_value = False
        with self._caplog.at_level(logging.ERROR):
            with raises(DistMigrationKernelRebootException):
                _get_cmdline(Defaults.get_grub_config_file())

    @patch('suse_migration_services.logger.Logger.setup')
    @patch('os.path.exists')
    def test_get_cmd_line(self, mock_path_exists, mock_logger_setup):
        mock_path_exists.return_value = True
        with open('../data/fake_grub.cfg') as fake_grub:
            fake_grub_data = fake_grub.read()
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.read.return_value = fake_grub_data
            grub_cmd_content = \
                'root=UUID=ec7aaf92-30ea-4c07-991a-4700177ce1b8 ' + \
                'splash root=UUID=ec7aaf92-30ea-4c07-991a-4700177ce1b8 rw'
            result = _get_cmdline(
                os.path.basename(Defaults.get_target_kernel())
            )
            mock_open.assert_called_once_with(
                '/system-root/boot/grub2/grub.cfg'
            )
            assert result == grub_cmd_content

    @patch('suse_migration_services.logger.Logger.setup')
    @patch('os.path.exists')
    def test_get_cmd_line_linuxefi(self, mock_path_exists, mock_logger_setup):
        mock_path_exists.return_value = True
        with open('../data/fake_grub_linuxefi.cfg') as fake_grub:
            fake_grub_data = fake_grub.read()
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.read.return_value = fake_grub_data
            grub_cmd_content = \
                'root=UUID=ec7aaf92-30ea-4c07-991a-4700177ce1b8 ' + \
                'splash root=UUID=ec7aaf92-30ea-4c07-991a-4700177ce1b8 rw'
            result = _get_cmdline(
                os.path.basename(Defaults.get_target_kernel())
            )
            mock_open.assert_called_once_with(
                '/system-root/boot/grub2/grub.cfg'
            )
            assert result == grub_cmd_content

    @patch('suse_migration_services.logger.Logger.setup')
    @patch('os.path.exists')
    def test_get_cmd_line_linux_variable(
        self, mock_path_exists, mock_logger_setup
    ):
        mock_path_exists.return_value = True
        with open('../data/fake_grub_linux_var.cfg') as fake_grub:
            fake_grub_data = fake_grub.read()
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.read.return_value = fake_grub_data
            grub_cmd_content = \
                'root=UUID=ec7aaf92-30ea-4c07-991a-4700177ce1b8 ' + \
                'splash root=UUID=ec7aaf92-30ea-4c07-991a-4700177ce1b8 rw'
            result = _get_cmdline(
                os.path.basename(Defaults.get_target_kernel())
            )
            mock_open.assert_called_once_with(
                '/system-root/boot/grub2/grub.cfg'
            )
            assert result == grub_cmd_content

    @patch('suse_migration_services.logger.Logger.setup')
    @patch('os.path.exists')
    def test_get_cmd_line_extra_boot_partition(
        self, mock_path_exists, mock_logger_setup
    ):
        mock_path_exists.return_value = True
        with open('../data/fake_grub_with_bootpart.cfg') as fake_grub:
            fake_grub_data = fake_grub.read()
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.read.return_value = fake_grub_data
            grub_cmd_content = \
                'root=UUID=ec7aaf92-30ea-4c07-991a-4700177ce1b8 ' + \
                'splash root=UUID=ec7aaf92-30ea-4c07-991a-4700177ce1b8 rw'
            result = _get_cmdline(
                os.path.basename(Defaults.get_target_kernel())
            )
            mock_open.assert_called_once_with(
                '/system-root/boot/grub2/grub.cfg'
            )
            assert result == grub_cmd_content

    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('shutil.copy')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.kernel_load._get_cmdline')
    def test_main_raises_on_kernel_load(
        self, mock_get_cmdline, mock_Command_run, mock_shutil_copy,
        mock_logger_setup, mock_get_migration_config_file
    ):
        cmd_line = \
            'root=UUID=ec7aaf92-30ea-4c07-991a-4700177ce1b8' + \
            'splash root=UUID=ec7aaf92-30ea-4c07-991a-4700177ce1b8 rw'
        mock_get_cmdline.return_value = cmd_line
        mock_get_migration_config_file.return_value = \
            '../data/migration-config.yml'
        mock_Command_run.side_effect = [
            None,
            Exception('error')
        ]
        with self._caplog.at_level(logging.ERROR):
            with raises(DistMigrationKernelRebootException):
                main()
        assert mock_Command_run.call_args_list == [
            call(
                ['mkdir', '-p', '/var/tmp/kexec']
            ),
            call(
                [
                    'kexec',
                    '--load', '/system-root/boot/vmlinuz',
                    '--initrd', '/var/tmp/kexec/initrd',
                    '--kexec-file-syscall',
                    '--command-line', cmd_line
                ]
            )
        ]

    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('shutil.copy')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.kernel_load._get_cmdline')
    def test_main(
        self, mock_get_cmdline, mock_Command_run, mock_shutil_copy,
        mock_logger_setup, mock_get_migration_config_file
    ):
        cmd_line = \
            'root=UUID=ec7aaf92-30ea-4c07-991a-4700177ce1b8' + \
            'splash root=UUID=ec7aaf92-30ea-4c07-991a-4700177ce1b8 rw'
        mock_get_cmdline.return_value = cmd_line
        mock_get_migration_config_file.return_value = \
            '../data/migration-config.yml'
        main()
        assert mock_Command_run.call_args_list == [
            call(
                ['mkdir', '-p', '/var/tmp/kexec']
            ),
            call(
                [
                    'kexec',
                    '--load', '/system-root/boot/vmlinuz',
                    '--initrd', '/var/tmp/kexec/initrd',
                    '--kexec-file-syscall',
                    '--command-line', cmd_line
                ]
            )
        ]

    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('shutil.copy')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.kernel_load._get_cmdline')
    def test_main_hard_reboot(
        self, mock_get_cmdline, mock_Command_run, mock_shutil_copy,
        mock_logger_setup, mock_get_migration_config_file
    ):
        cmd_line = \
            'root=UUID=ec7aaf92-30ea-4c07-991a-4700177ce1b8' + \
            'splash root=UUID=ec7aaf92-30ea-4c07-991a-4700177ce1b8 rw'
        mock_get_cmdline.return_value = cmd_line
        mock_get_migration_config_file.return_value = \
            '../data/migration-config-reboot.yml'
        main()
        assert mock_Command_run.call_args_list == []
