from unittest.mock import (
    patch, call, Mock
)
from pytest import raises

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


class TestMountSystem(object):
    @patch.object(Defaults, 'get_migration_log_file')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.mount_system.Path.create')
    @patch('os.path.exists')
    def test_main_system_already_mounted(
        self, mock_path_exists, mock_path_create,
        mock_Command_run, mock_info, mock_log_file
    ):
        mock_log_file.return_value = '../data/logfile'
        mock_path_exists.return_value = True
        command = Mock()
        command.returncode = 0
        mock_Command_run.return_value = command
        main()
        mock_path_create.assert_called_once_with('/system-root')
        assert mock_info.called

    @patch.object(Defaults, 'get_migration_log_file')
    @patch('suse_migration_services.logger.log.error')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.mount_system.Path.create')
    def test_main_no_system_found(
        self, mock_path_create, mock_Command_run,
        mock_info, mock_error, mock_log_file
    ):
        mock_log_file.return_value = '../data/logfile'
        with raises(DistMigrationSystemNotFoundException):
            main()
            assert mock_info.called
            assert mock_error.called

    @patch.object(Defaults, 'get_migration_log_file')
    @patch('suse_migration_services.logger.log.error')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.logger.log.warning')
    @patch('suse_migration_services.command.Command.run')
    def test_mount_system_raises(
            self, mock_Command_run, mock_warning, mock_info,
            mock_error, mock_log_file
    ):
        def command_calls(command):
            # mock error on mounting home, testing reverse umount
            if '/system-root/home' in command:
                raise Exception

        mock_log_file.return_value = '../data/logfile'
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
        assert mock_info.called
        assert mock_error.called

    @patch('yaml.safe_load')
    @patch('yaml.dump')
    @patch.object(Defaults, 'get_system_migration_custom_config_file')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch.object(MigrationConfig, 'update_migration_config_file')
    @patch.object(Defaults, 'get_migration_log_file')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.logger.log.set_logfile')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.mount_system.Path.create')
    @patch('suse_migration_services.units.mount_system.Path.wipe')
    @patch('suse_migration_services.units.mount_system.Fstab')
    @patch('suse_migration_services.units.mount_system.is_mounted')
    @patch('os.path.exists')
    def test_main(
        self, mock_path_exists, mock_is_mounted, mock_Fstab,
        mock_path_wipe, mock_path_create, mock_Command_run,
        mock_set_logfile, mock_info, mock_log_file,
        mock_update_migration_config_file, mock_get_migration_config_file,
        mock_get_system_migration_custom_config_file, mock_yaml_dump,
        mock_yaml_safe_load
    ):
        def _is_mounted(path):
            if path == '/run/initramfs/isoscan':
                return True
            return False

        mock_log_file.return_value = '../data/logfile'
        fstab = Fstab()
        fstab_mock = Mock()
        fstab_mock.read.return_value = fstab.read('../data/fstab')
        fstab_mock.get_devices.return_value = fstab.get_devices()
        mock_is_mounted.side_effect = _is_mounted
        mock_path_exists.side_effect = [True, True, False]
        mock_Fstab.return_value = fstab_mock
        command = Mock()
        command.returncode = 1
        command.output = '/dev/sda1 part'
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
                    ['mount', '/dev/sda1', '/system-root'], raise_on_error=False
                ),
                call(
                    ['umount', '/system-root'], raise_on_error=False),
                call(
                    [
                        'mount', '-o', 'acl,user_xattr',
                        '/dev/disk/by-uuid/'
                        'bd604632-663b-4d4c-b5b0-8d8686267ea2',
                        '/system-root/'
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
                        '/dev/disk/by-label/foo',
                        '/system-root/home'
                    ]
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
                    '/dev/disk/by-partuuid/3c8bd108-01',
                    '/system-root/bar',
                    'ext4'
                ),
                call(
                    '/dev/mynode',
                    '/system-root/foo',
                    'ext4'
                ),
                call(
                    'devtmpfs', '/system-root/dev'
                ),
                call(
                    '/proc', '/system-root/proc'
                ),
                call(
                    'sysfs', '/system-root/sys'
                )
            ]
            fstab_mock.export.assert_called_once_with(
                '/etc/system-root.fstab'
            )
            assert mock_open.call_args_list == [
                call('../data/logfile', 'w'),
                call('../data/migration-config.yml', 'r')
            ]
            mock_set_logfile.assert_called_once_with('../data/logfile'),
            assert mock_info.called
