from unittest.mock import (
    patch, call, Mock
)
from pytest import raises

from suse_migration_services.defaults import Defaults
from suse_migration_services.units.mount_system import (
    main, mount_system
)
from suse_migration_services.fstab import Fstab
from suse_migration_services.exceptions import (
    DistMigrationSystemNotFoundException,
    DistMigrationSystemMountException
)


class TestMountSystem(object):
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.mount_system.Path.create')
    def test_main_system_already_mounted(
        self, mock_path_create, mock_Command_run
    ):
        command = Mock()
        command.returncode = 0
        mock_Command_run.return_value = command
        main()
        mock_path_create.assert_called_once_with('/system-root')

    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.mount_system.Path.create')
    def test_main_no_system_found(
        self, mock_path_create, mock_Command_run
    ):
        with raises(DistMigrationSystemNotFoundException):
            main()

    @patch('suse_migration_services.command.Command.run')
    def test_mount_system_raises(self, mock_Command_run):
        def command_calls(command):
            # mock error on mounting home, testing reverse umount
            if '/system-root/home' in command:
                raise Exception

        mock_Command_run.side_effect = command_calls
        with raises(DistMigrationSystemMountException):
            fstab = Fstab()
            fstab.read('../data/fstab')
            mount_system(
                Defaults.get_system_root_path(), fstab
            )
        assert mock_Command_run.call_args_list == [
            call([
                'mount', '-o', 'acl,user_xattr',
                '/dev/disk/by-uuid/bd604632-663b-4d4c-b5b0-8d8686267ea2',
                '/system-root/'
            ]),
            call([
                'mount', '-o', 'defaults',
                '/dev/disk/by-uuid/FCF7-B051', '/system-root/boot/efi'
            ]),
            call([
                'mount', '-o', 'defaults',
                '/dev/disk/by-label/foo', '/system-root/home'
            ]),
            call(['umount', '/system-root/boot/efi']),
            call(['umount', '/system-root/'])
        ]

    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.mount_system.Path.create')
    @patch('suse_migration_services.units.mount_system.Fstab')
    @patch('os.path.exists')
    def test_main(
        self, mock_os_path_exists, mock_Fstab,
        mock_path_create, mock_Command_run
    ):
        fstab = Fstab()
        fstab_mock = Mock()
        fstab_mock.read.return_value = fstab.read('../data/fstab')
        fstab_mock.get_devices.return_value = fstab.get_devices()
        mock_os_path_exists.return_value = True
        mock_Fstab.return_value = fstab_mock
        command = Mock()
        command.output = '/dev/sda1 part'
        mock_Command_run.return_value = command
        main()
        assert mock_Command_run.call_args_list == [
            call(['mountpoint', '-q', '/system-root'], raise_on_error=False),
            call(['lsblk', '-p', '-n', '-r', '-o', 'NAME,TYPE']),
            call(['mount', '/dev/sda1', '/system-root'], raise_on_error=False),
            call(['umount', '/system-root'], raise_on_error=False),
            call([
                'mount', '-o', 'acl,user_xattr',
                '/dev/disk/by-uuid/bd604632-663b-4d4c-b5b0-8d8686267ea2',
                '/system-root/'
            ]),
            call([
                'mount', '-o', 'defaults',
                '/dev/disk/by-uuid/FCF7-B051',
                '/system-root/boot/efi'
            ]),
            call([
                'mount', '-o', 'defaults',
                '/dev/disk/by-label/foo',
                '/system-root/home'
            ]),
            call([
                'mount', '-o', 'defaults',
                '/dev/mynode',
                '/system-root/foo'
            ])]
        assert fstab_mock.add_entry.call_args_list == [
            call(
                '/dev/disk/by-uuid/bd604632-663b-4d4c-b5b0-8d8686267ea2',
                '/system-root/',
                'ext4'
            ),
            call(
                '/dev/disk/by-uuid/FCF7-B051',
                '/system-root/boot/efi',
                'vfat',
            ),
            call(
                '/dev/disk/by-label/foo',
                '/system-root/home',
                'ext4'
            ),
            call(
                '/dev/mynode',
                '/system-root/foo',
                'ext4'
            )
        ]
        fstab_mock.export.assert_called_once_with(
            '/etc/system-root.fstab'
        )
