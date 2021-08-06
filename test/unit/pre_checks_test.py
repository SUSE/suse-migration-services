import logging
from pytest import fixture
from unittest.mock import (
    patch, Mock
)

from suse_migration_services.prechecks.pre_checks import main
from suse_migration_services.fstab import Fstab
import suse_migration_services.prechecks.repos as check_repos


class TestPreChecks():
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('configparser.RawConfigParser.items')
    @patch('os.listdir')
    @patch('os.path.exists')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.prechecks.fs.Fstab')
    def test_main(
        self, mock_fstab, mock_command_run, mock_logger_setup, mock_os_exists,
        mock_os_listdir, mock_configparser_items
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
            main()
            assert warning_message_remote_repos in self._caplog.text
            assert warning_message_show_repos in self._caplog.text

    @patch('suse_migration_services.logger.Logger.setup')
    @patch('os.listdir')
    @patch('os.path.exists')
    def test_empty_repos(self, mock_os_exists, mock_os_listdir, mock_log):
        mock_os_exists.return_value = True
        mock_os_listdir.return_value = []
        check_repos.remote_repos()
