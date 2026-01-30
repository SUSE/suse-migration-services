from unittest.mock import patch, call
from pytest import fixture
from suse_migration_services.units.update_bootloader import main


class TestUpdateBootloader:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.zypper.Zypper.install')
    @patch('suse_migration_services.command.Command.run')
    def test_main(self, mock_Command_run, mock_Zypper_install, mock_logger_setup):
        main()
        mock_Zypper_install.assert_called_once_with('shim', system_root='/system-root')
        assert mock_Command_run.call_args_list == [
            call(['chroot', '/system-root', 'shim-install', '--removable'], raise_on_error=False),
            call(['chroot', '/system-root', '/sbin/update-bootloader', '--reinit']),
        ]
