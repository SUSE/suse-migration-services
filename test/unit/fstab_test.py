from collections import namedtuple

from suse_migration_services.fstab import Fstab


class TestFstab(object):
    def setup(self):
        self.fstab = Fstab('../data/fstab')

    def test_get_devices(self):
        fstab_entry_type = namedtuple(
            'fstab_entry_type', ['mountpoint', 'device', 'options']
        )
        assert self.fstab.get_devices() == [
            fstab_entry_type(
                mountpoint='/',
                device='/dev/disk/by-uuid/bd604632-663b-4d4c-b5b0-8d8686267ea2',
                options='acl,user_xattr'
            ),
            fstab_entry_type(
                mountpoint='swap',
                device='/dev/disk/by-uuid/daa5a8c3-5c72-4343-a1d4-bb74ec4e586e',
                options='defaults'
            ),
            fstab_entry_type(
                mountpoint='/boot/efi',
                device='/dev/disk/by-uuid/FCF7-B051',
                options='defaults'
            ),
            fstab_entry_type(
                mountpoint='/home',
                device='/dev/disk/by-label/foo',
                options='defaults'
            ),
            fstab_entry_type(
                mountpoint='/foo',
                device='/dev/mynode',
                options='defaults'
            )
        ]
