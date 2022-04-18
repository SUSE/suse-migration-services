import logging
from pytest import fixture
from unittest.mock import (
    patch, Mock
)

from suse_migration_services.fstab import Fstab
import suse_migration_services.prechecks.repos as check_repos
import suse_migration_services.prechecks.fs as check_fs
import suse_migration_services.prechecks.kernels as check_kernels
from suse_migration_services.exceptions import DistMigrationCommandException


@patch('suse_migration_services.logger.Logger.setup')
class TestPreChecks():
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('os.listdir')
    @patch('os.path.exists')
    @patch('configparser.RawConfigParser.items')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.prechecks.fs.Fstab')
    def test_main(
        self, mock_fstab, mock_command_run, mock_configparser_items,
        mock_os_exists, mock_os_listdir, mock_log
    ):
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
        mock_os_listdir.return_value = ['no_remote.repo', 'super_repo.repo', 'another.repo']
        repo_no_foo = 'hd:/?device=/dev/disk/by-uuid/bd604632-663b-4d4c-b5b0-8d8686267ea2'
        repo_no_bar = 'hd:/?device=/dev/disk/by-uuid/bd604632-663b-4d4c-b5b0-8d8686267ea4'
        mock_configparser_items.side_effect = [
            [('name', 'Foo'), ('enabled', '1'), ('autorefresh', '0'), ('baseurl', 'https://download.foo.com/foo/repo/'), ('type', 'rpm-md')],
            [('name', 'No_Foo'), ('enabled', '1'), ('autorefresh', '0'), ('baseurl', f"{repo_no_foo}"), ('path', '/'), ('keeppackages', '0')],
            [('name', 'No_Bar'), ('enabled', '1'), ('autorefresh', '0'), ('baseurl', f"{repo_no_bar}"), ('path', '/'), ('keeppackages', '0')]
        ]
        warning_message_remote_repos = \
            'The following repositories may cause the migration to fail, as they ' \
            'may not be available during the migration'
        warning_message_show_repos = \
            'To see all the repositories and their urls, you can run "zypper repos --url"'

        with self._caplog.at_level(logging.WARNING):
            check_repos.remote_repos()
            check_fs.encryption()
            assert warning_message_remote_repos in self._caplog.text
            assert warning_message_show_repos in self._caplog.text

    @patch('os.listdir')
    @patch('os.path.exists')
    def test_empty_repos(self, mock_os_exists, mock_os_listdir, mock_log):
        mock_os_exists.return_value = True
        mock_os_listdir.return_value = []
        check_repos.remote_repos()

    @patch('configparser.ConfigParser.get')
    @patch('suse_migration_services.command.Command.run')
    def test_multiple_kernels_default(
        self, mock_command_run, mock_configparser_items, mock_log
    ):
        """ Test for multiple kernel-default packages installed"""
        rpm_command = Mock()
        rpm_command.returncode = 0
        rpm_command.output = \
            'kernel-default-4.12.14-122.106.1.x86_64\nkernel-default-4.12.14-122.113.1.x86_64'

        uname_command = Mock()
        uname_command.returncode = 0
        uname_command.output = '4.12.14-122.113-default'

        mock_command_run.side_effect = [uname_command, rpm_command]

        mock_configparser_items.side_effect = ('multiversion.kernels', 'latest,running')

        warning_message_multipe_kernels = \
            'Multiple kernels have been detected on the system:'

        with self._caplog.at_level(logging.WARNING):
            check_kernels.multiversion_and_multiple_kernels()
            assert warning_message_multipe_kernels in self._caplog.text

    @patch('configparser.ConfigParser.get')
    @patch('suse_migration_services.command.Command.run')
    def test_multiple_kernels_azure(
        self, mock_command_run, mock_configparser_items, mock_log
    ):
        """ Test for multiple kernel-azure packages installed"""

        rpm_command = Mock()
        rpm_command.returncode = 0
        rpm_command.output = \
            'kernel-azure-4.12.14-16.85.1.x86_64\nkernel-azure-4.12.14-16.91.1.x86_64'

        uname_command = Mock()
        uname_command.returncode = 0
        uname_command.output = '4.12.14-16.85-azure'

        mock_command_run.side_effect = [uname_command, rpm_command]

        mock_configparser_items.side_effect = ('multiversion.kernels', 'latest,running')

        warning_message_multipe_kernels = \
            'Multiple kernels have been detected on the system:'

        with self._caplog.at_level(logging.WARNING):
            check_kernels.multiversion_and_multiple_kernels()
            assert warning_message_multipe_kernels in self._caplog.text

    @patch('configparser.ConfigParser.get')
    @patch('suse_migration_services.command.Command.run')
    def test_multiple_kernels_azure_with_fix(
        self, mock_command_run, mock_configparser_items, mock_log
    ):
        """ Test for multiple kernel-azure packages installed"""

        rpm_command = Mock()
        rpm_command.returncode = 0
        rpm_command.output = \
            'kernel-azure-4.12.14-16.85.1.x86_64\nkernel-azure-4.12.14-16.91.1.x86_64'

        uname_command = Mock()
        uname_command.returncode = 0
        uname_command.output = '4.12.14-16.85-azure'

        command = Mock()
        command.returncode = 0

        mock_command_run.side_effect = [uname_command, rpm_command, command]

        mock_configparser_items.return_value = 'latest,running'

        warning_message_multipe_kernels = \
            'Multiple kernels have been detected on the system:'

        with self._caplog.at_level(logging.WARNING):
            check_kernels.multiversion_and_multiple_kernels(True)
            assert warning_message_multipe_kernels in self._caplog.text

    @patch('configparser.ConfigParser.get')
    @patch('suse_migration_services.command.Command.run')
    def test_incorrect_multiversion_kernels_in_zypp_config(
        self, mock_command_run, mock_configparser_get, mock_log
    ):
        """ Test for incorrect setting in /etc/zypp/zypp.conf"""

        rpm_command = Mock()
        rpm_command.returncode = 0
        rpm_command.output = 'kernel-default-4.12.14-122.113.1.x86_64'

        uname_command = Mock()
        uname_command.returncode = 0
        uname_command.output = '4.12.14-122.113-default'

        mock_command_run.side_effect = [uname_command, rpm_command]

        mock_configparser_get.side_effect = ['kernel', 'latest,running,latest-1']

        warning_message_multipe_kernels = \
            'The config option multiversion.kernels is not set correctly'

        with self._caplog.at_level(logging.WARNING):
            check_kernels.multiversion_and_multiple_kernels()
            assert warning_message_multipe_kernels in self._caplog.text

    @patch('configparser.ConfigParser.get')
    @patch('suse_migration_services.command.Command.run')
    def test_missing_multiversion_kernels_in_zypp_config(
        self, mock_command_run, mock_configparser_get, mock_log
    ):
        """ Test for missing setting in /etc/zypp/zypp.conf"""
        rpm_command = Mock()
        rpm_command.returncode = 0
        rpm_command.output = 'kernel-default-4.12.14-122.113.1.x86_64'

        uname_command = Mock()
        uname_command.returncode = 0
        uname_command.output = '4.12.14-122.113-default'

        mock_command_run.side_effect = [uname_command, rpm_command]

        mock_configparser_get.side_effect = ['kernel', None]

        warning_message_multipe_kernels = \
            'Missing multiversion.kernels setting in zypp.conf'

        with self._caplog.at_level(logging.WARNING):
            check_kernels.multiversion_and_multiple_kernels()
            assert warning_message_multipe_kernels in self._caplog.text

    @patch('configparser.ConfigParser.get')
    @patch('suse_migration_services.command.Command.run')
    def test_update_zypp_conf_exception_raised(
        self, mock_command_run, mock_configparser_get, mock_log
    ):
        """ Test for error updating /etc/zypp/zypp.conf"""

        rpm_command = Mock()
        rpm_command.returncode = 0
        rpm_command.output = \
            'kernel-default-4.12.14-122.113.1.x86_64'

        uname_command = Mock()
        uname_command.returncode = 0
        uname_command.output = '4.12.14-122.113-default'

        mock_command_run.side_effect = [DistMigrationCommandException('Run failure'), uname_command, rpm_command, ]

        mock_configparser_get.side_effect = ['kernel', 'latest,running,latest-1']

        with self._caplog.at_level(logging.WARNING):
            check_kernels.multiversion_and_multiple_kernels(True)
            assert 'ERROR: Unable to update /etc/zypp/zypp.conf' in self._caplog.text

    @patch('configparser.ConfigParser.get')
    @patch('suse_migration_services.command.Command.run')
    def test_rpm_remove_exception_raised(
        self, mock_command_run, mock_configparser_get, mock_log
    ):
        """ Test for missing setting in /etc/zypp/zypp.conf"""
        rpm_command = Mock()
        rpm_command.returncode = 0
        rpm_command.output = \
            'kernel-default-4.12.14-122.106.1.x86_64\nkernel-default-4.12.14-122.113.1.x86_64'

        uname_command = Mock()
        uname_command.returncode = 0
        uname_command.output = '4.12.14-122.113-default'

        mock_command_run.side_effect = [uname_command, rpm_command, DistMigrationCommandException('Run failure')]

        mock_configparser_get.return_value = 'foo'

        with self._caplog.at_level(logging.WARNING):
            check_kernels.multiversion_and_multiple_kernels(True)
            assert 'ERROR: Unable to remove old kernel(s)' in self._caplog.text
