import io
from unittest.mock import patch, call, Mock
from pytest import raises

from suse_migration_services.units.setup_name_resolver import main, SetupNameResolver
from suse_migration_services.exceptions import DistMigrationNameResolverException


class TestSetupNameResolver:
    @patch('suse_migration_services.logger.Logger.setup')
    def setup(self, mock_Logger_setup):
        self.name_resolver = SetupNameResolver()
        self.name_resolver.root_path = '/system-root'
        self.name_resolver.resolv_conf = '/system-root/etc/resolv.conf'

    @patch('suse_migration_services.logger.Logger.setup')
    def setup_method(self, cls, mock_Logger_setup):
        self.setup()

    @patch(
        'suse_migration_services.units.setup_name_resolver.SetupNameResolver.has_host_resolv_setup'
    )
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.setup_name_resolver.Fstab')
    @patch('os.path.exists')
    @patch('shutil.copy')
    def test_main_raises_on_name_resolver_setup(
        self,
        mock_shutil_copy,
        mock_os_path_exists,
        mock_Fstab,
        mock_Command_run,
        mock_logger_setup,
        mock_resolv_empty,
    ):
        mock_os_path_exists.return_value = True
        mock_Command_run.side_effect = Exception
        mock_resolv_empty.return_value = False
        with raises(DistMigrationNameResolverException):
            main()
        assert not mock_shutil_copy.called

    @patch(
        'suse_migration_services.units.setup_name_resolver.SetupNameResolver.has_host_resolv_setup'
    )
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.setup_name_resolver.Fstab')
    @patch('os.path.exists')
    @patch('shutil.copy')
    @patch('glob.glob')
    @patch('os.path.isfile')
    def test_main(
        self,
        mock_isfile,
        mock_glob,
        mock_shutil_copy,
        mock_os_path_exists,
        mock_Fstab,
        mock_Command_run,
        mock_logger_setup,
        mock_empty_resolv,
    ):
        fstab = Mock()
        mock_Fstab.return_value = fstab
        mock_glob.return_value = [
            '/system-root/etc/sysconfig/network/ifcfg-eth0',
            '/system-root/etc/sysconfig/network/dhcp',
        ]
        mock_isfile.return_value = True
        mock_os_path_exists.return_value = True
        mock_empty_resolv.return_value = True
        main()

        assert mock_shutil_copy.call_args_list == [
            call('/system-root/etc/resolv.conf', '/etc/resolv.conf')
        ]

    def test_resolv_empty_with_info(self):
        with patch(
            'builtins.open', return_value=io.StringIO('# foo\n# bar\nsearch domain'), create=True
        ):
            assert self.name_resolver.has_host_resolv_setup() is True

    def test_resolv_empty_without_info(self):
        with patch(
            'suse_migration_services.units.setup_name_resolver.open',
            return_value=io.StringIO('#foo\n#bar\n'),
            create=True,
        ):
            assert self.name_resolver.has_host_resolv_setup() is False

    @patch(
        'suse_migration_services.units.setup_name_resolver.SetupNameResolver.has_host_resolv_setup'
    )
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.units.setup_name_resolver.Fstab')
    @patch('os.path.exists')
    @patch('shutil.copy')
    @patch('os.path.isfile')
    def test_main_bind_mount_resolv(
        self,
        mock_isfile,
        mock_shutil_copy,
        mock_os_path_exists,
        mock_Fstab,
        mock_Command_run,
        mock_logger_setup,
        mock_empty_resolv,
    ):
        fstab = Mock()
        mock_Fstab.return_value = fstab
        mock_isfile.return_value = True
        mock_os_path_exists.return_value = True
        mock_empty_resolv.return_value = False
        main()

        assert mock_Command_run.call_args_list == [
            call(['mount', '--bind', '/etc/resolv.conf', '/system-root/etc/resolv.conf']),
        ]
        fstab.add_entry.assert_has_calls(
            [
                call('/etc/resolv.conf', '/system-root/etc/resolv.conf'),
            ]
        )
        fstab.read.assert_any_call('/etc/system-root.fstab')
        fstab.export.assert_called_with('/etc/system-root.fstab')
