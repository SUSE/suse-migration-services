import io
import logging
from pytest import fixture
from unittest.mock import (
    MagicMock, patch, call, Mock
)
from suse_migration_services.fstab import Fstab


class TestFstab(object):
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('suse_migration_services.command.Command.run')
    @patch('os.path.exists')
    def setup(self, mock_os_path_exists, mock_Command_run):
        mock_os_path_exists.return_value = True

        def is_on_root_entries(command):
            command_on_root = Mock()
            command_on_root.returncode = 0
            skip_uuid = '/dev/disk/by-uuid/00d53ca7-11a4-4455-848e-ee52b1173518'

            if skip_uuid in command:
                command_on_root.output = 'sdb'
            else:
                command_on_root.output = 'sda'

            return command_on_root

        mock_Command_run.side_effect = is_on_root_entries
        self.fstab = Fstab()
        self.fstab.read('../data/fstab')
        print(self.fstab.root_disk)

    @patch('os.path.realpath')
    @patch('suse_migration_services.fstab.Fstab._is_on_root')
    @patch('suse_migration_services.fstab.Fstab._get_root_disk')
    @patch('suse_migration_services.command.Command.run')
    @patch('os.path.exists')
    def test_read_with_skipped_entries(
        self, mock_os_path_exists, mock_Command_run,
        mock_get_root_disk, mock_is_on_root, mock_os_realpath
    ):
        mock_os_path_exists.return_value = False
        mock_get_root_disk.return_value = 'sda'

        def is_on_root_entries(entry):
            skip_uuid = '00d53ca7-11a4-4455-848e-ee52b1173518'

            if skip_uuid in entry:
                return False

            return True

        def real_path(device):
            return device

        mock_is_on_root.side_effect = is_on_root_entries
        mock_os_realpath.side_effect = real_path
        fstab = Fstab()
        with self._caplog.at_level(logging.WARNING):
            fstab.read('../data/fstab')
            assert 'Device path /dev/mynode not found and skipped' in \
                self._caplog.text
        assert fstab.get_devices() == [
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/',
                device='/dev/disk/by-uuid/bd604632-663b-4d4c-b5b0-8d8686267ea2',
                options='acl,user_xattr',
                unix_device='/dev/disk/by-uuid/bd604632-663b-4d4c-b5b0-8d8686267ea2'
            ),
            self.fstab.fstab_entry_type(
                fstype='vfat',
                mountpoint='/boot/efi',
                device='/dev/disk/by-uuid/FCF7-B051',
                options='defaults',
                unix_device='/dev/disk/by-uuid/FCF7-B051'
            ),
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/home',
                device='/dev/disk/by-label/foo',
                options='defaults',
                unix_device='/dev/disk/by-label/foo'
            ),
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/bar',
                device='/dev/disk/by-partuuid/3c8bd108-01',
                options='defaults',
                unix_device='/dev/disk/by-partuuid/3c8bd108-01'
            )
        ]

    @patch('os.path.realpath')
    @patch('suse_migration_services.fstab.Fstab._is_on_root')
    def test_get_devices(self, mock_is_on_root, mock_os_realpath):
        def is_on_root_entries(entry):
            skip_uuid = '00d53ca7-11a4-4455-848e-ee52b1173518'

            if skip_uuid in entry:
                return False

            return True

        def real_path(device):
            return device

        mock_is_on_root.side_effect = is_on_root_entries
        mock_os_realpath.side_effect = real_path
        assert self.fstab.get_devices() == [
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/',
                device='/dev/disk/by-uuid/bd604632-663b-4d4c-b5b0-8d8686267ea2',
                options='acl,user_xattr',
                unix_device='/dev/disk/by-uuid/bd604632-663b-4d4c-b5b0-8d8686267ea2'
            ),
            self.fstab.fstab_entry_type(
                fstype='vfat',
                mountpoint='/boot/efi',
                device='/dev/disk/by-uuid/FCF7-B051',
                options='defaults',
                unix_device='/dev/disk/by-uuid/FCF7-B051'
            ),
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/home',
                device='/dev/disk/by-label/foo',
                options='defaults',
                unix_device='/dev/disk/by-label/foo'
            ),
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/bar',
                device='/dev/disk/by-partuuid/3c8bd108-01',
                options='defaults',
                unix_device='/dev/disk/by-partuuid/3c8bd108-01'
            ),
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/foo',
                device='/dev/mynode',
                options='defaults',
                unix_device='/dev/mynode'
            )
        ]

    @patch('suse_migration_services.fstab.Fstab._is_on_root')
    @patch('os.path.realpath')
    def test_add_entry(self, mock_os_realpath, mock_is_on_root):
        fstab = Fstab()
        mock_os_realpath.return_value = '/dev/sda'
        mock_is_on_root.return_value = True
        fstab.add_entry('/dev/sda', '/foo')
        assert fstab.get_devices() == [
            fstab.fstab_entry_type(
                fstype='none',
                mountpoint='/foo',
                device='/dev/sda',
                options='defaults',
                unix_device='/dev/sda'
            )
        ]

    @patch('suse_migration_services.fstab.Fstab._is_on_root')
    def test_export(self, mock_is_on_root):
        fstab = Fstab()
        fstab.add_entry('/dev/sda', '/foo')

        def is_on_root_entries(device):
            skip_uuid = '/dev/disk/by-uuid/00d53ca7-11a4-4455-848e-ee52b1173518'

            if skip_uuid in device:
                return False

            return True

        mock_is_on_root.side_effect = is_on_root_entries
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            fstab.export('filename')
            file_handle = mock_open.return_value.__enter__.return_value
            mock_open.assert_called_once_with(
                'filename', 'w'
            )
            assert file_handle.write.call_args_list == [
                call('/dev/sda /foo none defaults 0 0 /dev/sda\n')
            ]
