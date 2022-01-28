from unittest.mock import (
    patch, call, Mock
)
from pytest import raises
from collections import namedtuple
import logging

from suse_migration_services.defaults import Defaults
from suse_migration_services.units.mount_system import (
    main, mount_system
)
from suse_migration_services.migration_config import MigrationConfig
from suse_migration_services.fstab import Fstab
from suse_migration_services.exceptions import (
    DistMigrationSystemNotFoundException,
    DistMigrationSystemMountException
)


@patch('suse_migration_services.logger.Logger.setup')
@patch('suse_migration_services.units.mount_system.Path.create')
class TestMountSystem(object):
    @patch('os.path.ismount')
    def test_main_system_already_mounted(
        self, mock_path_ismount, mock_path_create, mock_logger_setup
    ):
        mock_path_ismount.return_value = True
        logger = logging.getLogger(Defaults.get_migration_log_name())
        with patch.object(logger, 'info') as mock_info:
            main()
            mock_path_create.assert_called_once_with('/system-root')
            assert mock_info.call_args_list == [
                call('Running mount system service'),
                call('Checking /system-root is mounted')
            ]

    @patch('suse_migration_services.command.Command.run')
    def test_main_no_system_found(
        self, mock_Command_run, mock_path_create, mock_logger_setup
    ):
        command_run = namedtuple(
            'command', ['output', 'error', 'returncode']
        )

        def command_calls(command):
            if 'lsblk' in command:
                return command_run(
                    output='/dev/sda4 part',
                    error='',
                    returncode=0
                )

        mock_Command_run.side_effect = command_calls

        with raises(DistMigrationSystemNotFoundException):
            main()

    @patch('os.path.exists')
    @patch('suse_migration_services.command.Command.run')
    def test_mount_system_raises(
        self, mock_Command_run, mock_os_path_exists,
        mock_path_create, mock_logger_setup
    ):
        def skip_device(device):
            if '/dev/mynode' in device:
                return False
            return True

        def command_calls(command):
            # mock error on mounting home
            if '/system-root/home' in command:
                raise Exception

        mock_os_path_exists.side_effect = skip_device
        mock_Command_run.side_effect = command_calls
        with raises(DistMigrationSystemMountException):
            fstab = Fstab()
            fstab.read('../data/fstab')
            mount_system(
                Defaults.get_system_root_path(), fstab
            )
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'mount', '-o', 'defaults',
                    '/dev/disk/by-partuuid/3c8bd108-01', '/system-root/bar'
                ]
            ),
            call(
                [
                    'mount', '-o', 'defaults',
                    '/dev/disk/by-label/foo', '/system-root/home'
                ]
            )
        ]

    @patch('yaml.safe_load')
    @patch('yaml.dump')
    @patch.object(Defaults, 'get_system_migration_custom_config_file')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch.object(MigrationConfig, 'update_migration_config_file')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.mount_system.Path.wipe')
    @patch('suse_migration_services.units.mount_system.Fstab')
    @patch('suse_migration_services.units.mount_system.is_mounted')
    @patch('os.path.isfile')
    @patch('os.path.exists')
    def test_main(
        self, mock_path_exists, mock_path_isfile, mock_is_mounted, mock_Fstab,
        mock_path_wipe, mock_Command_run, mock_update_migration_config_file,
        mock_get_migration_config_file,
        mock_get_system_migration_custom_config_file, mock_yaml_dump,
        mock_yaml_safe_load, mock_path_create, mock_logger_setup
    ):
        def _is_mounted(path):
            if path == '/run/initramfs/isoscan':
                return True
            return False

        fstab = Fstab()
        fstab_mock = Mock()
        fstab_mock.read.return_value = fstab.read('../data/fstab')
        fstab_mock.get_devices.return_value = fstab.get_devices()
        mock_is_mounted.side_effect = _is_mounted
        mock_path_exists.return_value = True
        mock_path_isfile.side_effect = [False, True]
        mock_Fstab.return_value = fstab_mock
        command = Mock()
        command.returncode = 1
        command.output = '/dev/sda1 part\n/dev/mapper/LVRoot lvm'
        mock_Command_run.return_value = command
        mock_get_system_migration_custom_config_file.return_value = \
            '../data/optional-migration-config.yml'
        mock_get_migration_config_file.return_value = \
            '../data/migration-config.yml'
        mock_yaml_safe_load.return_value = {
            'migration_product': 'SLES/15/x86_64'
        }
        with patch('builtins.open', create=True) as mock_open:
            main()
            assert mock_update_migration_config_file.called
            assert mock_Command_run.call_args_list == [
                call(
                    ['mount', '-o', 'remount,rw', '/run/initramfs/isoscan']
                ),
                call(
                    ['lsblk', '-p', '-n', '-r', '-o', 'NAME,TYPE']
                ),
                call(
                    ['vgchange', '-a', 'y']
                ),
                call(
                    ['mount', '/dev/sda1', '/system-root']
                ),
                call(
                    ['umount', '/system-root'], raise_on_error=False
                ),
                call(
                    ['mount', '/dev/mapper/LVRoot', '/system-root']
                ),
                call(
                    [
                        'mount', '-o', 'defaults',
                        '/dev/disk/by-partuuid/3c8bd108-01',
                        '/system-root/bar'
                    ]
                ),
                call(
                    [
                        'mount', '-o', 'defaults',
                        '/dev/mynode',
                        '/system-root/foo'
                    ]
                ),
                call(
                    [
                        'mount', '-o', 'defaults',
                        '/dev/disk/by-label/foo',
                        '/system-root/home'
                    ]
                ),
                call(
                    [
                        'mount', '-o', 'defaults',
                        '/dev/disk/by-uuid/FCF7-B051',
                        '/system-root/boot/efi'
                    ]
                ),
                call(
                    [
                        'mount', '-o', 'defaults',
                        '/dev/homeboy',
                        '/system-root/home/stack'
                    ]
                ),
                call(
                    ['mount', '-t', 'devtmpfs', 'devtmpfs', '/system-root/dev']
                ),
                call(
                    ['mount', '-t', 'proc', 'proc', '/system-root/proc']
                ),
                call(
                    ['mount', '-t', 'sysfs', 'sysfs', '/system-root/sys']
                )
            ]
            assert fstab_mock.add_entry.call_args_list == [
                call(
                    '/dev/disk/by-uuid/bd604632-663b-4d4c-b5b0-8d8686267ea2',
                    '/system-root/',
                    'ext4',
                    False,
                ),
                call(
                    '/dev/disk/by-partuuid/3c8bd108-01',
                    '/system-root/bar',
                    'ext4',
                    True
                ),
                call(
                    '/dev/mynode',
                    '/system-root/foo',
                    'ext4',
                    True
                ),
                call(
                    '/dev/disk/by-label/foo',
                    '/system-root/home',
                    'ext4',
                    True
                ),
                call(
                    '/dev/disk/by-uuid/FCF7-B051',
                    '/system-root/boot/efi',
                    'vfat',
                    True
                ),
                call(
                    '/dev/homeboy',
                    '/system-root/home/stack',
                    'ext4',
                    True
                ),
                call(
                    'devtmpfs', '/system-root/dev'
                ),
                call(
                    'proc', '/system-root/proc'
                ),
                call(
                    'sysfs', '/system-root/sys'
                )
            ]
            fstab_mock.export.assert_called_once_with(
                '/etc/system-root.fstab'
            )
            assert mock_open.call_args_list == [
                call('../data/migration-config.yml', 'r')
            ]
