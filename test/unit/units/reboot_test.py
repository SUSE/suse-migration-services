from unittest.mock import (
    patch, call
)

from suse_migration_services.units.reboot import main


class TestKernelReboot(object):
    @patch('suse_migration_services.command.Command.run')
    def test_main(self, mock_Command_run):
        main()
        mock_Command_run.assert_called_once_with(
            ['kexec', '--exec']
        )
        mock_Command_run.reset_mock()
        mock_Command_run.side_effect = [
            Exception,
            None
        ]
        main()
        assert mock_Command_run.call_args_list == [
            call(['kexec', '--exec']),
            call(['reboot', '-f'])
        ]
