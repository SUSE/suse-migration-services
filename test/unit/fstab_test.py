import io
import logging
from pytest import fixture
from unittest.mock import (
    MagicMock, patch, call
)
from suse_migration_services.fstab import Fstab


class TestFstab(object):
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('os.path.exists')
    def setup_method(self, method, mock_os_path_exists):
        mock_os_path_exists.return_value = True
        self.fstab = Fstab()
        self.fstab.read('../data/fstab')

    @patch('os.path.exists')
    def test_read_with_skipped_entries(self, mock_os_path_exists):
        def skip_device(device):
            if '/dev/mynode' in device:
                return False
            return True

        mock_os_path_exists.side_effect = skip_device
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
                options='',
                eligible_for_mount=False
            ),
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/bar',
                device='/dev/disk/by-partuuid/3c8bd108-01',
                options='defaults',
                eligible_for_mount=True
            ),
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/home',
                device='/dev/disk/by-label/foo',
                options='defaults',
                eligible_for_mount=True
            ),
            self.fstab.fstab_entry_type(
                fstype='vfat',
                mountpoint='/boot/efi',
                device='/dev/disk/by-uuid/FCF7-B051',
                options='defaults',
                eligible_for_mount=True
            ),
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/home/stack',
                device='/dev/homeboy',
                options='defaults',
                eligible_for_mount=True
            )
        ]

    def test_get_devices(self):
        assert self.fstab.get_devices() == [
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/',
                device='/dev/disk/by-uuid/bd604632-663b-4d4c-b5b0-8d8686267ea2',
                options='',
                eligible_for_mount=False
            ),
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/bar',
                device='/dev/disk/by-partuuid/3c8bd108-01',
                options='defaults',
                eligible_for_mount=True
            ),
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/foo',
                device='/dev/mynode',
                options='defaults',
                eligible_for_mount=True
            ),
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/home',
                device='/dev/disk/by-label/foo',
                options='defaults',
                eligible_for_mount=True
            ),
            self.fstab.fstab_entry_type(
                fstype='vfat',
                mountpoint='/boot/efi',
                device='/dev/disk/by-uuid/FCF7-B051',
                options='defaults',
                eligible_for_mount=True
            ),
            self.fstab.fstab_entry_type(
                fstype='ext4',
                mountpoint='/home/stack',
                device='/dev/homeboy',
                options='defaults',
                eligible_for_mount=True
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
                options='defaults',
                eligible_for_mount=True
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
