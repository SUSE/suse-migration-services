from unittest.mock import (
    patch, call
)
import os

from suse_migration_services.units.ssh_keys import main
from suse_migration_services.defaults import Defaults


@patch('suse_migration_services.logger.Logger.setup')
@patch('glob.glob')
class TestSSHKeys(object):
    def test_migration_continues_on_error(
        self, mock_glob_glob, mock_logger_setup
    ):
        mock_glob_glob.return_value = []
        main()  # expect pass and comment

    @patch('suse_migration_services.command.Command.run')
    @patch('shutil.copy')
    @patch.object(Defaults, 'get_system_sshd_config_path')
    @patch.object(Defaults, 'get_ssh_keys_paths')
    @patch.object(Defaults, 'get_migration_ssh_file')
    def test_main(
        self, mock_get_migration_ssh_file, mock_get_ssh_key_path,
        mock_get_system_sshd_config_path, mock_shutil_copy,
        mock_Command_run, mock_glob_glob, mock_logger_setup
    ):
        mock_get_ssh_key_path.return_value = ['/path/']
        mock_get_migration_ssh_file.return_value = '../data/authorized_keys'
        mock_glob_glob.side_effect = [
            [
                '../data/authorized_azure_keys',
                '../data/authorized_ec2_keys'
            ],
            [
                '/system-root/etc/ssh/ssh_host_ecdsa_key.pub',
                '/system-root/etc/ssh/ssh_host_ecdsa_key',
                '/system-root/etc/ssh/ssh_host_key'
            ]
        ]
        mock_get_system_sshd_config_path.return_value = '../data/sshd_config'
        main()
        output_file = mock_get_migration_ssh_file()
        expected_content = 'keys for azure\nkeys for aws ec2\n'
        with open(output_file) as ssh_output_file:
            assert expected_content == ssh_output_file.read()
        os.remove(output_file)

        expected_host_keys = '{}HostKey ../data/ssh_host_ecdsa_key'.format(
            os.linesep
        )
        with open(mock_get_system_sshd_config_path()) as sshd_config_file:
            assert expected_host_keys == sshd_config_file.read()
        os.remove(mock_get_system_sshd_config_path())

        assert mock_shutil_copy.call_args_list == [
            call('/system-root/etc/ssh/ssh_host_ecdsa_key.pub', '/etc/ssh/'),
            call('/system-root/etc/ssh/ssh_host_ecdsa_key', '/etc/ssh/')
        ]

        mock_Command_run.assert_called_once_with(
            ['systemctl', 'restart', 'sshd']
        )
