from unittest.mock import (
    patch, call, Mock
)
from pytest import raises
import yaml
import os

from suse_migration_services.defaults import Defaults
from suse_migration_services.units.mount_system import (
    main, mount_system, initialize_migration_config,
    _read_yml_file
)
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
    @patch('suse_migration_services.command.Command.run')
    def test_mount_system_raises(
            self, mock_Command_run, mock_info,
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
        mock_path_wipe, mock_path_create, mock_Command_run, mock_set_logfile,
        mock_info, mock_log_file
    ):
        def _is_mounted(path):
            if path == '/run/initramfs/isoscan':
                return True
            return False

        def _exist(path):
            if path == Defaults.get_system_migration_config_file():
                return False
            return True

        mock_log_file.return_value = '../data/logfile'
        fstab = Fstab()
        fstab_mock = Mock()
        fstab_mock.read.return_value = fstab.read('../data/fstab')
        fstab_mock.get_devices.return_value = fstab.get_devices()
        mock_is_mounted.side_effect = _is_mounted
        mock_path_exists.side_effect = _exist
        mock_Fstab.return_value = fstab_mock
        command = Mock()
        command.returncode = 1
        command.output = '/dev/sda1 part'
        mock_Command_run.return_value = command
        with patch('builtins.open', create=True) as mock_open:
            main()
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
                        '/dev/mynode',
                        '/system-root/foo'
                    ]
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
                    '/dev/mynode',
                    '/system-root/foo',
                    'ext4'
                )
            ]
            fstab_mock.export.assert_called_once_with(
                '/etc/system-root.fstab'
            )
            mock_open.assert_called_once_with('../data/logfile', 'w')
            mock_set_logfile.assert_called_once_with('../data/logfile')
            assert mock_info.called

    @patch('yaml.dump')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch.object(Defaults, 'get_system_migration_config_file')
    @patch('suse_migration_services.logger.log.info')
    @patch('os.path.exists')
    def test_initialize_migration_config_merge_contents(
        self, mock_path_exists, mock_info,
        mock_get_system_migration_config_file,
        mock_get_migration_config_file, mock_yaml
    ):
        migration_config_path = '../data/migration-config.yml'
        new_migration_config_path = '../data/system_migration_service.yml'
        merged_config_path = '../data/config_files_merged.yml'
        mock_get_migration_config_file.side_effect = [
            migration_config_path,
            merged_config_path
        ]
        mock_get_system_migration_config_file.return_value = \
            new_migration_config_path

        mock_path_exists.return_value = True
        initialize_migration_config()
        with open(merged_config_path) as merged_file:
            merged_values = yaml.safe_load(merged_file)
        with open(migration_config_path) as migration_config_file:
            migration_config_values = yaml.safe_load(migration_config_file)

        with open(new_migration_config_path) as new_config_file:
            new_config_values = yaml.safe_load(new_config_file)

        assert merged_values == migration_config_values.update(new_config_values)
        os.remove(merged_config_path)

    @patch('yaml.safe_load')
    @patch.object(Defaults, 'get_system_migration_config_file')
    @patch('suse_migration_services.logger.log.error')
    @patch('os.path.exists')
    def test_read_bad_yaml_config_file(
        self, mock_path_exists, mock_error,
        mock_get_system_migration_config_file, mock_yaml_safe_load
    ):
        mock_get_system_migration_config_file.return_value = \
            '../data/system_migration_service.yml'
        mock_yaml_safe_load.side_effect = Exception
        mock_path_exists.return_value = True

        _read_yml_file(mock_get_system_migration_config_file)
        assert mock_error.called
