import io
from unittest.mock import (
    MagicMock, patch, call
)
from suse_migration_services.fstab import Fstab


class TestFstab(object):
    def setup(self):
        self.fstab = Fstab()
        self.fstab.read('../data/fstab')

    def test_get_devices(self):
        assert self.fstab.get_devices() == [
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/',
                device='/dev/disk/by-uuid/bd604632-663b-4d4c-b5b0-8d8686267ea2',
                options='acl,user_xattr'
            ),
            self.fstab.fstab_entry_type(
                fstype='vfat',
                mountpoint='/boot/efi',
                device='/dev/disk/by-uuid/FCF7-B051',
                options='defaults'
            ),
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/home',
                device='/dev/disk/by-label/foo',
                options='defaults'
            ),
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/foo',
                device='/dev/mynode',
                options='defaults'
            )
        ]

    def test_add_entry(self):
        fstab = Fstab()
        fstab.add_entry('/dev/sda', '/foo')
        assert fstab.get_devices() == [
            fstab.fstab_entry_type(
                fstype='none',
                mountpoint='/foo',
                device='/dev/sda',
                options='defaults'
            )
        ]

    def test_export(self):
        fstab = Fstab()
        fstab.add_entry('/dev/sda', '/foo')
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            fstab.export('filename')
            file_handle = mock_open.return_value.__enter__.return_value
            mock_open.assert_called_once_with(
                'filename', 'w'
            )
            assert file_handle.write.call_args_list == [
                call('/dev/sda /foo none defaults 0 0\n')
            ]
