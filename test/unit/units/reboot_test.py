from unittest.mock import (
    patch, call, MagicMock
)
from suse_migration_services.units.reboot import main, _read_system_migration_config
import yaml


class TestKernelReboot(object):
    def test_read_system_migration_config(self):
        result = _read_system_migration_config('../data/system_migration_service.yml')
        assert result == {'debug': True, 'migration': 'migration'}

    @patch('suse_migration_services.units.reboot._read_system_migration_config')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    def test_main_skip_reboot_due_to_debug_file_set(
        self, mock_Command_run, mock_info, mock_read_values
    ):
        with open('../data/system_migration_service.yml') as fake_config:
            fake_config = yaml.load(fake_config)
        main()
        assert mock_info.called

    @patch('suse_migration_services.units.reboot.is_debug_mode')
    @patch('os.path.exists')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    def test_main_kexec_reboot(
        self, mock_Command_run, mock_info, mock_path_exists, mock_mode
    ):
        mock_path_exists.return_value = False
        mock_mode.return_value = False
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
