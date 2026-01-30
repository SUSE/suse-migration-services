from pytest import fixture
from unittest.mock import patch, call

from suse_migration_services.units.post_mount_system import main, PostMountSystem

from suse_migration_services.defaults import Defaults


class TestPostMountSystem(object):
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('suse_migration_services.logger.Logger.setup')
    def setup(self, mock_Logger_setup):
        self.post_mount_os = PostMountSystem()

    @patch('suse_migration_services.logger.Logger.setup')
    def setup_method(self, cls, mock_Logger_setup):
        self.setup()

    @patch('os.remove')
    @patch('os.path.isfile')
    @patch('glob.glob')
    @patch('os.path.exists')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.defaults.Defaults.get_system_root_path')
    @patch('shutil.copy')
    def test_main(
        self,
        mock_shutil_copy,
        mock_get_system_root_path,
        mock_Command_run,
        mock_logger_setup,
        mock_get_migration_config_file,
        mock_os_path_exists,
        mock_glob,
        mock_os_isfile,
        mock_os_remove,
    ):
        mock_get_system_root_path.return_value = '../data'
        mock_get_migration_config_file.return_value = '../data/migration-config.yml'
        mock_os_path_exists.side_effect = [True, False, True, False, True]
        mock_os_isfile.return_value = True

        def mock_glob_patterns(glob):
            if '*' in glob:
                ret = [glob.replace('*', 'a'), glob.replace('*', 'b')]
            else:
                ret = [glob]
            return ret

        mock_glob.side_effect = mock_glob_patterns

        main()
        assert mock_shutil_copy.call_args_list == [
            call('../data/etc/udev/rules.d/a.rules', '/etc/udev/rules.d'),
            call('../data/etc/udev/rules.d/b.rules', '/etc/udev/rules.d'),
            call('../data/etc/sysconfig/proxy', '/etc/sysconfig'),
            call('../data/etc/sysctl.conf', '/etc'),
        ]
        assert mock_Command_run.call_args_list == [
            call(['mkdir', '-p', '/etc/udev/rules.d']),
            call(['mkdir', '-p', '/etc/sysconfig']),
            call(['udevadm', 'control', '--reload']),
            call(['udevadm', 'trigger', '--type=subsystems', '--action=add']),
            call(['udevadm', 'trigger', '--type=devices', '--action=add']),
            call(['sysctl', '--system']),
        ]
        mock_os_remove.assert_called_once()
