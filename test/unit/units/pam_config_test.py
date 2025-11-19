from unittest.mock import (
    patch, call, mock_open
)

from suse_migration_services.units.pam_config import main
from suse_migration_services.defaults import Defaults


class TestPamConfig(object):
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('glob.glob')
    @patch('builtins.open')
    @patch.object(Defaults, 'get_system_root_path')
    def test_pam_config(
        self, mock_get_system_root_path,
        mock_builtin_open, mock_glob_glob, mock_logger_setup
    ):
        mock_get_system_root_path.return_value = '/system-root'
        mock_glob_glob.return_value = [
            '/system-root/etc/pam.d/mock_config_1',
            '/system-root/etc/pam.d/mock_config_2',
            '/system-root/etc/pam.d/mock_config_3'
        ]

        mock_handle_1 = mock_open(read_data='use pam_unix_auth.so').return_value
        mock_handle_2 = mock_open(
            read_data="use pam_unix_acct.so\nuse pam_unix_session.so"
        ).return_value
        mock_handle_3 = mock_open(read_data="use pam_unix.so").return_value

        mock_builtin_open.side_effect = [
            mock_handle_1,
            mock_handle_1,
            mock_handle_2,
            mock_handle_2,
            mock_handle_3,
            mock_handle_3
        ]

        main()

        mock_glob_glob.assert_called_once_with(
            '/system-root/etc/pam.d/*'
        )

        assert mock_builtin_open.call_args_list == [
            call('/system-root/etc/pam.d/mock_config_1', 'r'),
            call('/system-root/etc/pam.d/mock_config_1', 'w'),
            call('/system-root/etc/pam.d/mock_config_2', 'r'),
            call('/system-root/etc/pam.d/mock_config_2', 'w'),
            call('/system-root/etc/pam.d/mock_config_3', 'r'),
            call('/system-root/etc/pam.d/mock_config_3', 'w')
        ]

        mock_handle_1.write.assert_called_once_with(
            'use pam_unix.so'
        )

        mock_handle_2.write.assert_called_once_with(
            "use pam_unix.so\nuse pam_unix.so"
        )

        mock_handle_3.write.assert_called_once_with(
            "use pam_unix.so"
        )
