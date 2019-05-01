from unittest.mock import (
    patch, call, MagicMock
)
from suse_migration_services.units.reboot import main, is_debug_mode
from suse_migration_services.defaults import Defaults


class TestKernelReboot(object):
    @patch.object(Defaults, 'get_migration_config_file')
    def test_is_not_debug_mode(self, mock_get_migration_config_file):
        mock_get_migration_config_file.return_value = \
            '../data/migration-config.yml'

        result = is_debug_mode()
        assert not result

    @patch.object(Defaults, 'get_migration_config_file')
    def test_is_debug_mode(self, mock_get_migration_config_file):
        mock_get_migration_config_file.return_value = \
            '../data/system_migration_service.yml'

        result = is_debug_mode()
        assert result

    @patch('suse_migration_services.units.reboot.is_debug_mode')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    def test_main_skip_reboot_due_to_debug_file_set(
        self, mock_Command_run, mock_info, mock_is_debug_mode
    ):
        mock_is_debug_mode.return_value = True
        main()
        assert mock_info.called

    @patch('suse_migration_services.units.reboot.is_debug_mode')
    @patch('os.path.exists')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    def test_main_kexec_reboot(
        self, mock_Command_run, mock_info, mock_path_exists, mock_debug
    ):
        mock_debug.return_value = False
        main()
        assert mock_info.called
        assert mock_Command_run.call_args_list == [
            call(['systemctl', 'status', '-l', '--all'], raise_on_error=False),
            call(['kexec', '--exec'])
        ]

    @patch('suse_migration_services.units.reboot.is_debug_mode')
    @patch('suse_migration_services.logger.log.warning')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    def test_main_force_reboot(
        self, mock_Command_run, mock_info, mock_warning, mock_path_exists
    ):
        mock_Command_run.side_effect = [
            MagicMock(), Exception, None
        ]
        mock_path_exists.return_value = False
        main()
        assert mock_info.called
        assert mock_Command_run.call_args_list == [
            call(['systemctl', 'status', '-l', '--all'], raise_on_error=False),
            call(['kexec', '--exec']),
            call(['reboot', '-f'])
        ]
        mock_warning.assert_called_once_with(
            'Reboot system: [Force Reboot]'
        )
