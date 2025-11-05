import io
from unittest.mock import (
    patch, call, Mock, MagicMock
)
from pytest import raises
from collections import namedtuple

from suse_migration_services.units.mount_system import (
    main, mount_system, get_uuid, activate_lvm,
    get_target_root, is_mounted, read_system_fstab
)
from suse_migration_services.migration_config import MigrationConfig
from suse_migration_services.fstab import Fstab
from suse_migration_services.exceptions import (
    DistMigrationSystemNotFoundException,
    DistMigrationSystemMountException
)


class TestMountSystem():
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.units.mount_system.Path.create')
    @patch('suse_migration_services.units.mount_system.is_mounted')
    @patch('suse_migration_services.units.mount_system.mount_system')
    def test_main_root_already_mounted(
        self,
        mock_mount_system,
        mock_is_mounted,
        mock_Path_create,
        mock_Logger_setup
    ):
        mock_is_mounted.return_value = True
        main()
        mock_Path_create.assert_called_once_with('/system-root')
        assert not mock_mount_system.called

    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.units.mount_system.Path.create')
    @patch('suse_migration_services.units.mount_system.is_mounted')
    @patch('suse_migration_services.units.mount_system.mount_system')
    @patch('suse_migration_services.units.mount_system.read_system_fstab')
    @patch('suse_migration_services.units.mount_system.activate_lvm')
    @patch('suse_migration_services.command.Command.run')
    @patch.object(MigrationConfig, 'update_migration_config_file')
    def test_main_perform(
        self,
        mock_update_migration_config_file,
        mock_Command_run,
        mock_activate_lvm,
        mock_read_system_fstab,
        mock_mount_system,
        mock_is_mounted,
        mock_Path_create,
        mock_Logger_setup
    ):
        def _is_mounted(path):
            if path == '/run/initramfs/isoscan':
                return True
            return False

        mock_is_mounted.side_effect = _is_mounted
        main()
        mock_Command_run.assert_called_once_with(
            ['mount', '-o', 'remount,rw', '/run/initramfs/isoscan']
        )
        mock_mount_system.assert_called_once_with(
            '/system-root', mock_read_system_fstab.return_value
        )
        mock_update_migration_config_file.assert_called_once_with()
        mock_activate_lvm.assert_called_once_with()

    @patch('suse_migration_services.command.Command.run')
    def test_get_uuid(self, mock_Command_run):
        get_uuid('some')
        mock_Command_run.assert_called_once_with(
            ['blkid', 'some', '-s', 'UUID', '-o', 'value'],
            raise_on_error=False
        )

    @patch('suse_migration_services.command.Command.run')
    def test_activate_lvm(self, mock_Command_run):
        command_run = namedtuple(
            'command', ['output', 'error', 'returncode']
        )
        mock_Command_run.return_value = command_run(
            output='/dev/sda4 lvm',
            error='',
            returncode=0
        )
        activate_lvm()
        assert mock_Command_run.call_args_list == [
            call(['lsblk', '-p', '-n', '-r', '-o', 'NAME,TYPE']),
            call(['vgchange', '-a', 'y'])
        ]

    @patch('suse_migration_services.command.Command.run')
    def test_get_target_root_no_match_found(self, mock_Command_run):
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.read.return_value = 'foo'
            with raises(DistMigrationSystemMountException):
                get_target_root()

    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.mount_system.get_uuid')
    def test_get_target_root_match_found(
        self,
        mock_get_uuid,
        mock_Command_run
    ):
        mock_get_uuid.return_value = 'UUID'
        command_run = namedtuple(
            'command', ['output', 'error', 'returncode']
        )
        mock_Command_run.return_value = command_run(
            output='/dev/sda4 lvm',
            error='',
            returncode=0
        )
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.read.return_value = 'migration_target=UUID'
            assert get_target_root() == '/dev/sda4'

    @patch('suse_migration_services.logger.Logger.setup')
    @patch('os.path.ismount')
    def test_is_mounted(self, mock_os_path_ismount, mock_Logger_setup):
        is_mounted('some')
        mock_os_path_ismount.assert_called_once_with('some')

    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.units.mount_system.get_target_root')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.mount_system.Fstab')
    @patch('os.path.isfile')
    def test_read_system_fstab(
        self,
        mock_os_path_isfile,
        mock_Fstab,
        mock_Command_run,
        mock_get_target_root,
        mock_Logger_setup
    ):
        fstab = Mock()
        mock_Fstab.return_value = fstab
        # fstab file found
        mock_os_path_isfile.return_value = True
        assert read_system_fstab('some') == fstab
        mock_Command_run.assert_called_once_with(
            ['mount', mock_get_target_root.return_value, 'some']
        )
        # fstab file not found
        mock_os_path_isfile.return_value = False
        mock_Command_run.reset_mock()
        with raises(DistMigrationSystemNotFoundException):
            read_system_fstab('some')
        assert mock_Command_run.call_args_list == [
            call(['mount', mock_get_target_root.return_value, 'some']),
            call(['umount', 'some'], raise_on_error=False)
        ]

    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.mount_system.Fstab')
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_mount_system(
        self,
        mock_os_path_exists,
        mock_os_makedirs,
        mock_Fstab,
        mock_Command_run,
        mock_Logger_setup
    ):
        mock_os_path_exists.return_value = True
        fstab = Fstab()
        fstab_mock = Mock()
        fstab_mock.read.return_value = fstab.read('../data/fstab')
        fstab_mock.get_devices.return_value = fstab.get_devices()

        mount_system('some', fstab_mock)
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'mount', '-o', 'defaults',
                    '/dev/disk/by-partuuid/3c8bd108-01', 'some/bar'
                ]
            ),
            call(['mount', '-o', 'defaults', '/dev/mynode', 'some/foo']),
            call(
                [
                    'mount', '-o', 'defaults',
                    '/dev/disk/by-label/foo', 'some/home'
                ]
            ),
            call(
                [
                    'mount', '-o', 'defaults',
                    '/dev/disk/by-uuid/FCF7-B051', 'some/boot/efi'
                ]
            ),
            call(
                [
                    'mount', '-o', 'defaults',
                    '/dev/homeboy', 'some/home/stack'
                ]
            ),
            call(['mount', '-t', 'devtmpfs', 'devtmpfs', 'some/dev']),
            call(['mount', '-t', 'proc', 'proc', 'some/proc']),
            call(['mount', '-t', 'sysfs', 'sysfs', 'some/sys']),
            call(
                [
                    'mount', '-o', 'bind', '/run/NetworkManager',
                    'some/run/NetworkManager'
                ]
            ),
            call(
                [
                    'mount', '-o', 'bind', '/run/netconfig',
                    'some/run/netconfig'
                ]
            )
        ]
        mock_Command_run.side_effect = Exception
        with raises(DistMigrationSystemMountException):
            mount_system('some', fstab_mock)
