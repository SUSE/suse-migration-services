from unittest.mock import (
    patch
)
import os

from suse_migration_services.units.ssh_keys import main
from suse_migration_services.defaults import Defaults


class TestSshAccess(object):
    @patch('suse_migration_services.logger.log.error')
    @patch('glob.glob')
    def test_migration_continues_on_error(
        self, mock_glob_glob, mock_error
    ):
        mock_glob_glob.return_value = []
        mock_error.levelno = 40
        main()  # expect pass and comment
        assert mock_error.called

    @patch.object(Defaults, 'get_ssh_keys_paths')
    @patch('glob.glob')
    @patch.object(Defaults, 'get_migration_ssh_file')
    @patch('suse_migration_services.logger.log.info')
    def test_main(
        self, mock_info, mock_get_migration_ssh_file,
        mock_glob_glob, mock_glob_ssh
    ):
        mock_glob_ssh.return_value = ['/path/']
        mock_get_migration_ssh_file.return_value = '../data/authorized_keys'
        mock_glob_glob.return_value = [
            '../data/authorized_azure_keys',
            '../data/authorized_ec2_keys'
        ]
        main()
        output_file = mock_get_migration_ssh_file()
        expected_content = 'keys for azure\nkeys for aws ec2\n'
        with open(output_file) as ssh_output_file:
            assert expected_content == ssh_output_file.read()
        os.remove(output_file)
