from unittest.mock import patch, call, Mock
from pytest import fixture
from suse_migration_services.units.update_bootloader import main


class TestUpdateBootloader:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('suse_migration_services.units.update_bootloader.MigrationConfig')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.zypper.Zypper.install')
    @patch('suse_migration_services.command.Command.run')
    def test_main(
        self, mock_Command_run, mock_Zypper_install, mock_logger_setup, mock_MigrationConfig
    ):
        migration_config = Mock()
        migration_config.get_zypper_install_args.return_value = []
        mock_MigrationConfig.return_value = migration_config
        main()
        mock_Zypper_install.assert_called_once_with(
            'shim', system_root='/system-root', extra_args=[]
        )
        assert mock_Command_run.call_args_list == [
            call(['chroot', '/system-root', 'shim-install', '--removable'], raise_on_error=False),
            call(['chroot', '/system-root', '/sbin/update-bootloader', '--reinit']),
        ]
