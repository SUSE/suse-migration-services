import io
import argparse
import logging
import os
import subprocess
from unittest.mock import (
    patch, call, Mock, MagicMock
)
from pytest import fixture

from suse_migration_services.command import Command
from suse_migration_services.fstab import Fstab
import suse_migration_services.prechecks.repos as check_repos
import suse_migration_services.prechecks.fs as check_fs
import suse_migration_services.prechecks.kernels as check_kernels
import suse_migration_services.prechecks.scc as check_scc
import suse_migration_services.prechecks.ha as check_ha
import suse_migration_services.prechecks.pre_checks as check_pre_checks
from suse_migration_services.exceptions import DistMigrationCommandException
from suse_migration_services.defaults import Defaults


@patch('suse_migration_services.logger.Logger.setup')
@patch('os.geteuid')
class TestPreChecks():
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        """Setup capture for mock"""
        self._caplog = caplog

    @patch('suse_migration_services.prechecks.repos.remote_repos')
    @patch('suse_migration_services.prechecks.fs.encryption')
    @patch('suse_migration_services.prechecks.kernels.multiversion_and_multiple_kernels')
    @patch.dict(
        os.environ, {"SUSE_MIGRATION_PRE_CHECKS_MODE": "foo"}, clear=True
    )
    @patch(
        'argparse.ArgumentParser.parse_args',
        return_value=argparse.Namespace(fix=False)
    )
    def test_main(
        self, mock_arg_parse, mock_kernels,
        mock_fs, mock_repos, mock_os_geteuid, mock_log
    ):
        mock_os_geteuid.return_value = 0
        with self._caplog.at_level(logging.INFO):
            check_pre_checks.main()
            assert "Running suse-migration-pre-checks" in self._caplog.text

    @patch('suse_migration_services.prechecks.repos.remote_repos')
    @patch('suse_migration_services.prechecks.fs.encryption')
    @patch('suse_migration_services.prechecks.kernels.multiversion_and_multiple_kernels')
    @patch.dict(
        os.environ,
        {
            "SUSE_MIGRATION_PRE_CHECKS_MODE": "migration_system_iso_image"
        }, clear=True
    )
    @patch(
        'argparse.ArgumentParser.parse_args',
        return_value=argparse.Namespace(fix=True)
    )
    def test_main_with_fix_and_migration_system_mode(
        self, mock_arg_parse, mock_kernels, mock_fs,
        mock_repos, mock_os_geteuid, mock_log
    ):
        """
        Test calling main() when using fix and migration_system
        """
        mock_os_geteuid.return_value = 0
        with self._caplog.at_level(logging.INFO):
            check_pre_checks.main()
            assert "fix: True" in self._caplog.text
            assert "Using migration_system mode" in self._caplog.text

    @patch('os.listdir')
    @patch('os.path.exists')
    @patch('configparser.RawConfigParser.items')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.prechecks.fs.Fstab')
    def test_fs_and_repos(
        self, mock_fstab, mock_command_run, mock_configparser_items,
        mock_os_exists, mock_os_listdir, mock_os_geteuid, mock_log
    ):
        """
        Test fs and repo modules
        """
        def luks(device):
            command = Mock()
            command.returncode = 0
            command.output = 'ext4'
            if device[-1] == '/dev/disk/by-label/foo':
                command.output = 'crypto_LUKS'
            return command

        fstab = Fstab()
        fstab_mock = Mock()
        fstab_mock.read.return_value = fstab.read('../data/fstab')
        fstab_mock.get_devices.return_value = fstab.get_devices()
        mock_fstab.return_value = fstab_mock
        mock_command_run.side_effect = luks
        mock_os_exists.return_value = True
        mock_os_listdir.return_value = [
            'no_remote.repo', 'super_repo.repo', 'another.repo'
        ]
        repo_no_foo = \
            'hd:/?device=/dev/disk/by-uuid/bd604632-663b-4d4c-b5b0-8d8686267ea2'
        repo_no_bar = \
            'hd:/?device=/dev/disk/by-uuid/bd604632-663b-4d4c-b5b0-8d8686267ea4'
        mock_configparser_items.side_effect = [
            [
                ('name', 'Foo'),
                ('enabled', '1'),
                ('autorefresh', '0'),
                ('baseurl', 'https://download.foo.com/foo/repo/'),
                ('type', 'rpm-md')
            ],
            [
                ('name', 'No_Foo'),
                ('enabled', '1'),
                ('autorefresh', '0'),
                ('baseurl', f"{repo_no_foo}"),
                ('path', '/'),
                ('keeppackages', '0')
            ],
            [
                ('name', 'No_Bar'),
                ('enabled', '1'),
                ('autorefresh', '0'),
                ('baseurl', f"{repo_no_bar}"),
                ('path', '/'),
                ('keeppackages', '0')
            ]
        ]
        warning_message_remote_repos = \
            'The following repositories may cause the migration ' \
            'to fail, as they may not be available during the migration'
        warning_message_show_repos = \
            'To see all the repositories and their urls, you can ' \
            'run "zypper repos --url"'

        with self._caplog.at_level(logging.WARNING):
            check_repos.remote_repos()
            check_fs.encryption()
            assert warning_message_remote_repos in self._caplog.text
            assert warning_message_show_repos in self._caplog.text

    @patch('os.listdir')
    @patch('os.path.exists')
    @patch('configparser.RawConfigParser.items')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.prechecks.fs.Fstab')
    def test_fs_and_repos_with_migration_system(
        self, mock_fstab, mock_command_run, mock_configparser_items,
        mock_os_exists, mock_os_listdir, mock_os_geteuid, mock_log
    ):
        """
        Test fs and repo modules
        """
        def luks(device):
            command = Mock()
            command.returncode = 0
            command.output = 'ext4'
            if device[-1] == '/dev/disk/by-label/foo':
                command.output = 'crypto_LUKS'
            return command

        fstab = Fstab()
        fstab_mock = Mock()
        fstab_mock.read.return_value = fstab.read('../data/fstab')
        fstab_mock.get_devices.return_value = fstab.get_devices()
        mock_fstab.return_value = fstab_mock
        mock_command_run.side_effect = luks
        mock_os_exists.return_value = True
        mock_os_listdir.return_value = [
            'no_remote.repo', 'super_repo.repo', 'another.repo'
        ]
        repo_no_foo = \
            'hd:/?device=/dev/disk/by-uuid/bd604632-663b-4d4c-b5b0-8d8686267ea2'
        repo_no_bar = \
            'hd:/?device=/dev/disk/by-uuid/bd604632-663b-4d4c-b5b0-8d8686267ea4'
        mock_configparser_items.side_effect = [
            [
                ('name', 'Foo'),
                ('enabled', '1'),
                ('autorefresh', '0'),
                ('baseurl', 'https://download.foo.com/foo/repo/'),
                ('type', 'rpm-md')
            ],
            [
                ('name', 'No_Foo'),
                ('enabled', '1'),
                ('autorefresh', '0'),
                ('baseurl', f"{repo_no_foo}"),
                ('path', '/'),
                ('keeppackages', '0')
            ],
            [
                ('name', 'No_Bar'),
                ('enabled', '1'),
                ('autorefresh', '0'),
                ('baseurl', f"{repo_no_bar}"),
                ('path', '/'),
                ('keeppackages', '0')
            ]
        ]
        warning_message_remote_repos = \
            'The following repositories may cause the migration to ' \
            'fail, as they may not be available during the migration'
        warning_message_show_repos = \
            'To see all the repositories and their urls, you can ' \
            'run "zypper repos --url"'

        with self._caplog.at_level(logging.WARNING):
            check_repos.remote_repos(True)
            check_fs.encryption(True)
            assert warning_message_remote_repos in self._caplog.text
            assert warning_message_show_repos in self._caplog.text

    @patch('os.listdir')
    @patch('os.path.exists')
    def test_empty_repos(
        self, mock_os_exists, mock_os_listdir, mock_os_geteuid, mock_log
    ):
        """
        Test for empty repos
        """
        mock_os_exists.return_value = True
        mock_os_listdir.return_value = []
        check_repos.remote_repos()

    @patch('configparser.ConfigParser.get')
    @patch('suse_migration_services.command.Command.run')
    @patch('os.readlink')
    def test_multiple_kernels_default(
        self, mock_os_readlink, mock_command_run,
        mock_configparser_items, mock_os_geteuid, mock_log
    ):
        """
        Test for multiple kernel-default packages installed
        """
        mock_os_readlink.return_value = 'vmlinuz-4.12.14-122.113-default'

        rpm_command = Mock()
        rpm_command.returncode = 0
        rpm_command.output = \
            'kernel-default-4.12.14-122.106.1.x86_64\n' \
            'kernel-default-4.12.14-122.113.1.x86_64'

        mock_command_run.side_effect = [rpm_command]

        mock_configparser_items.side_effect = (
            'multiversion.kernels', 'latest,running'
        )
        warning_message_multipe_kernels = \
            'Multiple kernels have been detected on the system:'

        with self._caplog.at_level(logging.INFO):
            check_kernels.multiversion_and_multiple_kernels()
            assert warning_message_multipe_kernels in self._caplog.text

    @patch('configparser.ConfigParser.get')
    @patch('suse_migration_services.command.Command.run')
    @patch('os.readlink')
    def test_multiple_kernels_azure(
        self, mock_os_readlink, mock_command_run,
        mock_configparser_items, mock_os_geteuid, mock_log
    ):
        """
        Test for multiple kernel-azure packages installed
        """
        mock_os_readlink.return_value = 'vmlinuz-4.12.14-16.91-azure'

        rpm_command = Mock()
        rpm_command.returncode = 0
        rpm_command.output = \
            'kernel-azure-4.12.14-16.85.1.x86_64\n' \
            'kernel-azure-4.12.14-16.91.1.x86_64'

        mock_command_run.side_effect = [rpm_command]

        mock_configparser_items.side_effect = (
            'multiversion.kernels', 'latest,running'
        )
        warning_message_multipe_kernels = \
            'Please remove all kernels other than the currrent running kernel:'

        with self._caplog.at_level(logging.WARNING):
            check_kernels.multiversion_and_multiple_kernels()
            assert warning_message_multipe_kernels in self._caplog.text

    @patch('configparser.ConfigParser.get')
    @patch('suse_migration_services.command.Command.run')
    @patch('os.readlink')
    def test_multiple_kernels_azure_with_fix(
        self, mock_os_readlink, mock_command_run,
        mock_configparser_items, mock_os_geteuid, mock_log
    ):
        """
        Test for multiple kernel-azure packages installed
        """
        mock_os_readlink.return_value = 'vmlinuz-4.12.14-16.91-azure'

        rpm_command = Mock()
        rpm_command.returncode = 0
        rpm_command.output = \
            'kernel-azure-4.12.14-16.85.1.x86_64\n' \
            'kernel-azure-4.12.14-16.91.1.x86_64'

        command = Mock()
        command.returncode = 0

        mock_command_run.side_effect = [rpm_command, command]

        mock_configparser_items.return_value = 'latest,running'

        warning_message_multipe_kernels = \
            "The '--fix' option was provided, removing old kernels"

        with self._caplog.at_level(logging.INFO):
            check_kernels.multiversion_and_multiple_kernels(True)
            assert warning_message_multipe_kernels in self._caplog.text

    @patch('configparser.ConfigParser.get')
    @patch('suse_migration_services.command.Command.run')
    @patch('os.readlink')
    def test_incorrect_multiversion_kernels_in_zypp_config(
        self, mock_os_readlink, mock_command_run,
        mock_configparser_get, mock_os_geteuid, mock_log
    ):
        """
        Test for incorrect setting in /etc/zypp/zypp.conf
        """
        mock_os_readlink.return_value = 'vmlinuz-4.12.14-122.113-default'

        rpm_command = Mock()
        rpm_command.returncode = 0
        rpm_command.output = 'kernel-default-4.12.14-122.113.1.x86_64'

        mock_command_run.side_effect = [rpm_command]

        mock_configparser_get.side_effect = \
            ['provides:multiversion(kernel)', 'latest,running,latest-1']

        warning_message_multipe_kernels = \
            'The config option multiversion.kernels is not set correctly'

        with self._caplog.at_level(logging.WARNING):
            check_kernels.multiversion_and_multiple_kernels()
            assert warning_message_multipe_kernels in self._caplog.text

    @patch('configparser.ConfigParser.get')
    @patch('suse_migration_services.command.Command.run')
    @patch('os.readlink')
    def test_missing_multiversion_kernels_in_zypp_config(
        self, mock_os_readlink, mock_command_run,
        mock_configparser_get, mock_os_geteuid, mock_log
    ):
        """
        Test for missing setting in /etc/zypp/zypp.conf
        """
        mock_os_readlink.return_value = 'vmlinuz-4.12.14-122.113-default'

        rpm_command = Mock()
        rpm_command.returncode = 0
        rpm_command.output = 'kernel-default-4.12.14-122.113.1.x86_64'

        mock_command_run.side_effect = [rpm_command]

        mock_configparser_get.side_effect = \
            ['provides:multiversion(kernel)', None]

        warning_message_multipe_kernels = \
            'Missing multiversion.kernels setting in zypp.conf'

        with self._caplog.at_level(logging.WARNING):
            check_kernels.multiversion_and_multiple_kernels()
            assert warning_message_multipe_kernels in self._caplog.text

    @patch('configparser.ConfigParser.get')
    @patch('suse_migration_services.command.Command.run')
    @patch('os.readlink')
    def test_missing_multiversion_in_zypp_config(
        self, mock_os_readlink, mock_command_run,
        mock_configparser_get, mock_os_geteuid, mock_log
    ):
        """
        Test for missing setting in /etc/zypp/zypp.conf
        """
        mock_os_readlink.return_value = 'vmlinuz-4.12.14-122.113-default'

        rpm_command = Mock()
        rpm_command.returncode = 0
        rpm_command.output = 'kernel-default-4.12.14-122.113.1.x86_64'

        mock_command_run.side_effect = [rpm_command]

        mock_configparser_get.side_effect = \
            [None]

        warning_message_multipe_kernels = \
            "Could not find the config option 'multiversion' in " \
            "/etc/zypp/zypp.conf. Skipping check for " \
            "'multiversion.kernels'"

        with self._caplog.at_level(logging.INFO):
            check_kernels.multiversion_and_multiple_kernels()
            assert warning_message_multipe_kernels in self._caplog.text

    @patch('configparser.ConfigParser.get')
    @patch('suse_migration_services.command.Command.run')
    @patch('os.readlink')
    def test_update_zypp_conf_exception_raised(
        self, mock_os_readlink, mock_command_run,
        mock_configparser_get, mock_os_geteuid, mock_log
    ):
        """
        Test for error updating /etc/zypp/zypp.conf
        """
        mock_os_readlink.return_value = 'vmlinuz-4.12.14-122.113-default'

        rpm_command = Mock()
        rpm_command.returncode = 0
        rpm_command.output = \
            'kernel-default-4.12.14-122.113.1.x86_64'

        mock_command_run.side_effect = [
            DistMigrationCommandException('Run failure'), rpm_command
        ]
        mock_configparser_get.side_effect = \
            ['provides:multiversion(kernel)', 'latest,running,latest-1']

        with self._caplog.at_level(logging.WARNING):
            check_kernels.multiversion_and_multiple_kernels(True)
            assert 'ERROR: Unable to update /etc/zypp/zypp.conf' in \
                self._caplog.text

    @patch('configparser.ConfigParser.get')
    @patch('suse_migration_services.command.Command.run')
    @patch('os.readlink')
    def test_rpm_remove_exception_raised(
        self, mock_os_readlink, mock_command_run,
        mock_configparser_get, mock_os_geteuid, mock_log
    ):
        """
        Test for missing setting in /etc/zypp/zypp.conf
        """
        mock_os_readlink.return_value = 'vmlinuz-4.12.14-122.113-default'

        rpm_command = Mock()
        rpm_command.returncode = 0
        rpm_command.output = \
            'kernel-default-4.12.14-122.106.1.x86_64\n' \
            'kernel-default-4.12.14-122.113.1.x86_64'

        mock_command_run.side_effect = [
            rpm_command, DistMigrationCommandException('Run failure')
        ]
        mock_configparser_get.return_value = 'foo'
        with self._caplog.at_level(logging.WARNING):
            check_kernels.multiversion_and_multiple_kernels(True)
            assert 'ERROR: Unable to remove old kernel(s)' in self._caplog.text

    @patch('configparser.ConfigParser.get')
    @patch('suse_migration_services.command.Command.run')
    @patch('os.readlink')
    def test_correct_rpm_commands_when_using_target(
        self, mock_os_readlink, mock_command_run,
        mock_configparser_get, mock_os_geteuid, mock_log
    ):
        """
        Test for missing setting in /etc/zypp/zypp.conf
        """
        mock_os_readlink.return_value = 'vmlinuz-4.12.14-122.113-default'

        rpm_command = Mock()
        rpm_command.returncode = 0
        rpm_command.output = \
            'kernel-default-4.12.14-122.106.1.x86_64\n' \
            'kernel-default-4.12.14-122.113.1.x86_64'

        mock_command_run.side_effect = [rpm_command, rpm_command]
        mock_configparser_get.return_value = 'foo'
        check_kernels.multiversion_and_multiple_kernels(True, True)
        assert mock_command_run.call_args_list == [
            call(
                [
                    'chroot',
                    '/system-root',
                    'rpm',
                    '-qa',
                    'kernel-default'
                ]
            ),
            call(
                [
                    'chroot',
                    '/system-root',
                    'rpm',
                    '-e',
                    'kernel-default-4.12.14-122.106.1.x86_64'
                ]
            )
        ]

    @patch('configparser.ConfigParser.get')
    @patch('suse_migration_services.command.Command.run')
    @patch('os.readlink')
    def test_correct_rpm_command_when_using_target_with_azure(
        self, mock_os_readlink, mock_command_run,
        mock_configparser_get, mock_os_geteuid, mock_log
    ):
        """
        Test for missing setting in /etc/zypp/zypp.conf
        """
        mock_os_readlink.return_value = 'vmlinuz-4.12.14-16.91-azure'

        rpm_command = Mock()
        rpm_command.returncode = 0
        rpm_command.output = \
            'kernel-azure-4.12.14-16.91.1.x86_64'

        mock_command_run.side_effect = [rpm_command]

        mock_configparser_get.return_value = 'foo'

        check_kernels.multiversion_and_multiple_kernels(True, True)
        assert mock_command_run.call_args_list == [
            call(
                [
                    'chroot',
                    '/system-root',
                    'rpm',
                    '-qa',
                    'kernel-azure'
                ]
            ),
        ]

    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.prechecks.scc.migration')
    @patch('suse_migration_services.prechecks.repos.remote_repos')
    @patch('suse_migration_services.prechecks.fs.encryption')
    @patch('suse_migration_services.prechecks.kernels.multiversion_and_multiple_kernels')
    @patch.dict(
        os.environ, {
            "SUSE_MIGRATION_PRE_CHECKS_MODE": "migration_system_iso_image"
        }, clear=True
    )
    @patch(
        'argparse.ArgumentParser.parse_args',
        return_value=argparse.Namespace(fix=True)
    )
    def test_pre_checks_false(
        self, mock_argparse, mock_kernels, mock_fs,
        mock_repos, mock_scc_migration, mock_get_migration_config_file,
        mock_os_geteuid, mock_log
    ):
        """
        Test for missing setting in /etc/zypp/zypp.conf
        """
        mock_os_geteuid.return_value = 0
        mock_get_migration_config_file.return_value = \
            '../data/migration-config-pre-checks.yml'

        info_message = "Overriding the --fix option"
        with self._caplog.at_level(logging.INFO):
            check_pre_checks.main()
            assert info_message in self._caplog.text

    @patch('yaml.safe_load')
    @patch('glob.glob')
    @patch('os.path.isfile')
    @patch('requests.post')
    @patch.object(Command, 'run')
    @patch.object(Defaults, 'get_migration_config_file')
    def test_check_scc_migration(
        self, mock_get_migration_config_file,
        mock_Command_run, mock_requests_post,
        mock_os_path_isfile, mock_glob, mock_yaml_safe_load,
        mock_os_geteuid, mock_log
    ):
        response = Mock()
        response.json.return_value = {
            'type': 'error',
            'error': 'Some error'
        }
        mock_glob.return_value = ['../data/SLES.prod']
        mock_os_path_isfile.return_value = True
        mock_requests_post.return_value = response
        with patch('builtins.open', create=True) as mock_open:
            mock_open_credentials = MagicMock(spec=io.IOBase)
            mock_open_suseconnect = MagicMock(spec=io.IOBase)
            mock_open_migration_config = MagicMock(spec=io.IOBase)

            def safe_load_suseconnect_exception(handle):
                if handle == file_handle_suseconnect:
                    raise Exception('IO Error')
                elif handle == file_handle_migration_config:
                    return {'migration_product': 'SLES/15.3/x86_64'}

            def safe_load_migration_config_exception(handle):
                if handle == file_handle_suseconnect:
                    return {'url': 'https://smt-ec2.susecloud.net'}
                elif handle == file_handle_migration_config:
                    raise Exception('IO Error')

            def safe_load(handle):
                if handle == file_handle_suseconnect:
                    return {'url': 'https://smt-ec2.susecloud.net'}
                elif handle == file_handle_migration_config:
                    return {'migration_product': 'SLES/15.3/x86_64'}

            def open_file(filename, mode=None):
                if filename == '/etc/zypp/credentials.d/SCCcredentials':
                    return mock_open_credentials.return_value
                elif filename == '/etc/SUSEConnect':
                    return mock_open_suseconnect.return_value
                elif filename == '/etc/sle-migration-service.yml':
                    return mock_open_migration_config.return_value

            mock_open.side_effect = open_file

            file_handle_credentials = \
                mock_open_credentials.return_value.__enter__.return_value
            file_handle_suseconnect = \
                mock_open_suseconnect.return_value.__enter__.return_value
            file_handle_migration_config = \
                mock_open_migration_config.return_value.__enter__.return_value

            mock_yaml_safe_load.side_effect = safe_load

            file_handle_credentials.read.return_value = \
                'username=SCC_xxx\npassword=xxx\n'

            with self._caplog.at_level(logging.ERROR):
                check_scc.migration()
                mock_requests_post.assert_called_once_with(
                    'https://smt-ec2.susecloud.net/'
                    'connect/systems/products/offline_migrations',
                    json={
                        'installed_products': [
                            {
                                'identifier': 'SLES',
                                'version': '12.5',
                                'arch': 'x86_64'
                            }
                        ],
                        'target_base_product': {
                            'identifier': 'SLES',
                            'version': '15.3',
                            'arch': 'x86_64'
                        }
                    },
                    auth=('SCC_xxx', 'xxx'),
                    headers={
                        'accept': 'application/json',
                        'Content-Type': 'application/json'
                    }
                )
                assert 'Some error' in self._caplog.text

            # Test exception on requests.post
            mock_requests_post.side_effect = Exception('Some error')
            check_scc.migration()
            assert 'Post request to https://smt-ec2.susecloud.net '
            'failed with Some error' in self._caplog.text
            mock_requests_post.reset_mock()

            # Test exception on get_migration_target
            mock_yaml_safe_load.side_effect = \
                safe_load_migration_config_exception
            check_scc.migration()
            assert not mock_requests_post.called

            # Test exception on get_registration_server_url
            mock_yaml_safe_load.side_effect = \
                safe_load_suseconnect_exception
            check_scc.migration()
            assert not mock_requests_post.called

            # Test exception on get_scc_credentials
            mock_yaml_safe_load.side_effect = safe_load
            file_handle_credentials.read.side_effect = Exception('IO error')
            check_scc.migration()
            assert not mock_requests_post.called

    @patch('platform.machine')
    @patch('os.path.isfile')
    @patch.object(Command, 'run')
    def test_check_scc_migration_default_target(
        self, mock_Command_run, mock_os_path_isfile,
        mock_platform_machine, mock_os_geteuid, mock_log
    ):
        mock_platform_machine.return_value = 'x86_64'
        sles15_migration = Mock()
        sles15_migration.returncode = 0
        mock_Command_run.return_value = sles15_migration
        mock_os_path_isfile.return_value = False
        assert check_scc.get_migration_target() == {
            'identifier': 'SLES',
            'version': '15.3',
            'arch': 'x86_64'
        }

    @patch('platform.machine')
    @patch('os.path.isfile')
    @patch.object(Command, 'run')
    def test_check_scc_migration_default_target_sles16(
        self, mock_Command_run, mock_os_path_isfile,
        mock_platform_machine, mock_os_geteuid, mock_log
    ):
        mock_platform_machine.return_value = 'x86_64'
        sles15_migration_not_found = Mock()
        sles15_migration_not_found.returncode = 1  # SLES15-Migration not found
        sles16_migration_found = Mock()
        sles16_migration_found.returncode = 0  # SLES16-Migration found
        mock_Command_run.side_effect = [sles15_migration_not_found, sles16_migration_found]
        mock_os_path_isfile.return_value = False  # No /etc/sle-migration-service.yml
        assert check_scc.get_migration_target() == {
            'identifier': 'SLES',
            'version': '16.0',
            'arch': 'x86_64'
        }

    def test_privileges(self, mock_os_geteuid, mock_log):
        with self._caplog.at_level(logging.ERROR):
            check_pre_checks.main()
            assert 'pre-checks requires root permissions' in self._caplog.text

    @patch('subprocess.run')
    @patch('os.access')
    def test_check_ha_in_migration_system(
        self,
        mock_os_access, mock_subprocess_run,
        mock_os_getuid, mock_log,
    ):
        mock_os_access.return_value = False
        with self._caplog.at_level(logging.INFO):
            check_ha.check_ha(migration_system=True)
            assert 'Skipped checks for high availablity extension' in self._caplog.text
        mock_os_access.assert_not_called()
        mock_subprocess_run.assert_not_called()

    @patch('subprocess.run')
    @patch('os.access')
    def test_check_ha_not_intialzied(
        self,
        mock_os_access, mock_subprocess_run,
        mock_os_getuid, mock_log,
    ):
        mock_os_access.return_value = False
        with self._caplog.at_level(logging.INFO):
            check_ha.check_ha(migration_system=False)
            assert 'Skipped checks for high availablity extension' in self._caplog.text
        mock_subprocess_run.assert_not_called()

    @patch('subprocess.run')
    @patch('os.access')
    def test_check_ha_not_installed(
        self,
        mock_os_access, mock_subprocess_run,
        mock_os_getuid, mock_log,
    ):
        mock_os_access.return_value = True
        mock_subprocess_run.side_effect = FileNotFoundError()
        with self._caplog.at_level(logging.INFO):
            check_ha.check_ha(migration_system=False)
            assert 'Skipped checks for high availablity extension' in self._caplog.text
        mock_subprocess_run.assert_called_once()

    @patch('subprocess.run')
    @patch('os.access')
    def test_check_ha_unexpected_exception_when_calling_crmsh(
        self,
        mock_os_access, mock_subprocess_run,
        mock_os_getuid, mock_log,
    ):
        mock_os_access.return_value = True
        mock_subprocess_run.side_effect = PermissionError()
        with self._caplog.at_level(logging.WARNING):
            check_ha.check_ha(migration_system=False)
            assert 'Skipped checks for high availablity extension' in self._caplog.text
        mock_subprocess_run.assert_called_once()

    @patch('subprocess.run')
    @patch('os.access')
    def test_check_ha(
        self,
        mock_os_access, mock_subprocess_run,
        mock_os_getuid, mock_log,
    ):
        mock_os_access.return_value = True
        mock_subprocess_run.return_value = Mock(returncode=0, stdout=b'crm cluster health hawk2|sles16')
        with self._caplog.at_level(logging.INFO):
            check_ha.check_ha(migration_system=False)
            assert 'Skipped checks for high availablity extension.' not in self._caplog.text
        mock_subprocess_run.assert_has_calls([
            call(
                ['crm', 'help', 'cluster', 'health'],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            ),
            call(['crm', 'cluster', 'health', 'sles16', '--local']),
        ])
