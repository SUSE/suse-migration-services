from unittest.mock import (
    patch, call
)
from collections import namedtuple

from suse_migration_services.units.reboot import (
    main, _migration_has_failed
)


class TestKernelReboot(object):
    @patch('suse_migration_services.command.Command.run')
    def test_migration_has_failed(
        self, mock_Command_run
    ):
        command_type = namedtuple(
            'command', ['output', 'error', 'returncode']
        )
        result = command_type(
            output='failed\n',
            error='',
            returncode=1
        )
        mock_Command_run.return_value = result
        _migration_has_failed()
        mock_Command_run.assert_called_once_with(
            ['systemctl', 'is-failed', 'suse-migration']
        )

    @patch('suse_migration_services.units.reboot._migration_has_failed')
    @patch('os.path.exists')
    @patch('suse_migration_services.logger.log.warning')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    def test_main_not_reboot(
        self, mock_Command_run, mock_info, mock_warning,
        mock_path_exists, mock_migration_failed
    ):
        mock_path_exists.return_value = True
        mock_migration_failed.return_value = True
        main()
        assert mock_info.called
        assert not mock_Command_run.called

    @patch('suse_migration_services.units.reboot._migration_has_failed')
    @patch('os.path.exists')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    def test_main_failed_migration_reboot(
        self, mock_Command_run, mock_info,
        mock_path_exists, mock_migration_failed
    ):
        mock_migration_failed.return_value = True
        mock_path_exists.return_value = False
        main()
        mock_path_exists.assert_called_once_with(
            '/etc/sle-migration-service'
        )
        assert mock_info.called
        mock_Command_run.assert_called_once_with(
            ['kexec', '--exec']
        )

    @patch('suse_migration_services.units.reboot._migration_has_failed')
    @patch('os.path.exists')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    def test_main_not_remove_file_reboot(
        self, mock_Command_run, mock_info,
        mock_path_exists, mock_migration_failed
    ):
        mock_migration_failed.return_value = False
        mock_path_exists.return_value = False
        main()
        assert mock_info.called
        mock_Command_run.assert_called_once_with(
            ['kexec', '--exec']
        )

    @patch('os.path.exists')
    @patch('os.remove')
    @patch('suse_migration_services.defaults.Defaults.get_system_migration_debug_file')
    @patch('suse_migration_services.units.reboot._migration_has_failed')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    def test_main_remove_file_reboot(
        self, mock_Command_run, mock_info, mock_migration_failed,
        mock_get_system_migration_debug_file, mock_os_remove, mock_path_exists
    ):
        mock_migration_failed.return_value = False
        mock_path_exists.return_value = True
        mock_get_system_migration_debug_file.return_value = 'foo'
        main()
        assert mock_info.called
        mock_os_remove.assert_called_once_with('/foo')
        mock_Command_run.assert_called_once_with(
            ['kexec', '--exec']
        )

    @patch('suse_migration_services.units.reboot._migration_has_failed')
    @patch('suse_migration_services.logger.log.warning')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    def test_main_reboot_exception(
        self, mock_Command_run, mock_info,
        mock_warning, mock_migration_failed
    ):
        mock_migration_failed.return_value = True
        mock_Command_run.side_effect = [
            Exception,
            None
        ]
        main()
        assert mock_info.called
        assert mock_Command_run.call_args_list == [
            call(['kexec', '--exec']),
            call(['reboot', '-f'])
        ]
        mock_warning.assert_called_once_with('Forcing reboot')
