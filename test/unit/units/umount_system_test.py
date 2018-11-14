from unittest.mock import (
    patch, call, Mock
)

from suse_migration_services.units.umount_system import main
from suse_migration_services.fstab import Fstab


class TestUMountSystem(object):
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.umount_system.Fstab')
    @patch('os.path.exists')
    def test_main(
        self, mock_os_path_exists, mock_Fstab, mock_Command_run
    ):
        fstab = Fstab()
        fstab_mock = Mock()
        fstab_mock.read.return_value = fstab.read('../data/system-root.fstab')
        fstab_mock.get_devices.return_value = fstab.get_devices()
        mock_Fstab.return_value = fstab_mock
        mock_os_path_exists.return_value = True
        main()
        assert mock_Command_run.call_args_list == [
            call(['umount', '/etc/sysconfig/network'], raise_on_error=False),
            call(['umount', '/etc/zypp'], raise_on_error=False),
            call(['umount', '/system-root/foo'], raise_on_error=False),
            call(['umount', '/system-root/home'], raise_on_error=False),
            call(['umount', '/system-root/boot/efi'], raise_on_error=False),
            call(['umount', '/system-root/'], raise_on_error=False)
        ]
