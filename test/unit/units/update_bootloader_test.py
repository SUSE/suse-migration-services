from unittest.mock import (
    patch, call
)
from pytest import fixture
from suse_migration_services.units.update_bootloader import main


@patch('suse_migration_services.logger.Logger.setup')
class TestUpdateBootloader:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('suse_migration_services.zypper.Zypper.run')
    @patch('suse_migration_services.command.Command.run')
    def test_main(self, mock_Command_run, mock_Zypper_run, mock_logger_setup):
        main()
        mock_Zypper_run.assert_called_once_with(
            [
                '--no-cd',
                '--non-interactive',
                '--gpg-auto-import-keys',
                '--root', '/system-root',
                'install',
                '--auto-agree-with-licenses',
                '--allow-vendor-change',
                '--download', 'in-advance',
                '--replacefiles',
                '--allow-downgrade',
                'shim'
            ]
        )
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'chroot', '/system-root',
                    'shim-install', '--removable'
                ], raise_on_error=False
            ),
            call(
                [
                    'chroot', '/system-root',
                    '/sbin/update-bootloader', '--reinit'
                ]
            )
        ]
