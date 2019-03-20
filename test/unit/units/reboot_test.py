from unittest.mock import (
    patch, call
)
from suse_migration_services.units.reboot import main


class TestKernelReboot(object):
    @patch('os.path.exists')
    @patch('suse_migration_services.logger.log.warning')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    def test_main_skip_reboot_due_to_debug_file_set(
        self, mock_Command_run, mock_info, mock_warning, mock_path_exists
    ):
        mock_path_exists.return_value = True
        main()
        assert mock_info.called

    @patch('os.path.exists')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.path.Path.wipe')
    def test_main_kexec_reboot(
        self, mock_Path_wipe, mock_Command_run, mock_info, mock_path_exists
    ):
        mock_path_exists.return_value = False
        main()
        mock_path_exists.assert_called_once_with(
            '/etc/sle-migration-service'
        )
        assert mock_info.called
        mock_Path_wipe.assert_called_once_with(
            '/etc/sle-migration-service'
        )
        mock_Command_run.assert_called_once_with(
            ['kexec', '--exec']
        )

    @patch('suse_migration_services.logger.log.warning')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.path.Path.wipe')
    def test_main_force_reboot(
        self, mock_Path_wipe, mock_Command_run, mock_info, mock_warning
    ):
        mock_Command_run.side_effect = [
            Exception, None
        ]
        main()
        mock_Path_wipe.assert_called_once_with(
            '/etc/sle-migration-service'
        )
        assert mock_info.called
        assert mock_Command_run.call_args_list == [
            call(['kexec', '--exec']),
            call(['reboot', '-f'])
        ]
        mock_warning.assert_called_once_with(
            'Reboot system: [Force Reboot]'
        )
