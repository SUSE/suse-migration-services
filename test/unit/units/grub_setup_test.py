from unittest.mock import (
    patch, call, Mock
)
from pytest import raises

from suse_migration_services.units.grub_setup import main
from suse_migration_services.fstab import Fstab
from suse_migration_services.exceptions import (
    DistMigrationGrubConfigException
)


class TestSetupHostNetwork(object):
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.grub_setup.Fstab')
    def test_main_raises_on_grub_update(
        self, mock_Fstab, mock_Command_run
    ):
        fstab = Fstab()
        fstab_mock = Mock()
        fstab_mock.read.return_value = fstab.read('../data/bind-mounted.fstab')
        fstab_mock.get_devices.return_value = fstab.get_devices()
        fstab_mock.export.side_effect = Exception
        mock_Fstab.return_value = fstab_mock
        with raises(DistMigrationGrubConfigException):
            main()
            assert mock_Command_run.call_args_list == [
                call(['umount', '/system-root/dev'], raise_on_error=False),
                call(['umount', '/system-root/proc'], raise_on_error=False),
                call(['umount', '/system-root/sys'], raise_on_error=False)
            ]

    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.grub_setup.Fstab')
    def test_main(
        self, mock_Fstab, mock_Command_run
    ):
        fstab = Mock()
        mock_Fstab.return_value = fstab
        main()
        fstab.read.assert_called_once_with(
            '/etc/system-root.fstab'
        )
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'chroot', '/system-root',
                    'rpm', '-e', 'suse-migration-activation'
                ]
            ),
            call(
                [
                    'mount', '--bind', '/dev',
                    '/system-root/dev'
                ]
            ),
            call(
                [
                    'mount', '--bind', '/proc',
                    '/system-root/proc'
                ]
            ),
            call(
                [
                    'mount', '--bind', '/sys',
                    '/system-root/sys'
                ]
            ),
            call(
                [
                    'chroot', '/system-root',
                    'grub2-mkconfig', '-o', '/boot/grub2/grub.cfg'
                ]
            )
        ]
        fstab.add_entry.assert_has_calls(
            [
                call('/dev', '/system-root/dev'),
                call('/proc', '/system-root/proc'),
                call('/sys', '/system-root/sys')
            ]
        )
        fstab.export.assert_called_once_with(
            '/etc/system-root.fstab'
        )
