from unittest.mock import (
    patch, Mock
)

from suse_migration_services.prechecks.pre_checks import (
    main, check_remote_repos
)

from suse_migration_services.fstab import Fstab


class TestPreChecks(object):
    @patch('builtins.print')
    @patch('configparser.RawConfigParser.items')
    @patch('os.listdir')
    @patch('os.path.exists')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.prechecks.pre_checks.Fstab')
    def test_main(
        self, mock_Fstab, mock_Command_run, mock_logger_setup,
        mock_os_exists, mock_os_listdir, mock_configparser_items, mock_print
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
        mock_Fstab.return_value = fstab_mock
        mock_Command_run.side_effect = luks
        mock_os_exists.return_value = True
        mock_os_listdir.return_value = ['no_remote.repo', 'super_repo.repo']
        mock_configparser_items.side_effect = [
            [('name', 'Foo'), ('enabled', '1'), ('autorefresh', '0'), ('baseurl', 'https://download.foo.com/foo/repo/'), ('type', 'rpm-md')],
            [('name', 'No_Foo'), ('enabled', '1'), ('autorefresh', '0'), ('baseurl', 'hd:/?device=/dev/disk/by-uuid/bd604632-663b-4d4c-b5b0-8d8686267ea2'), ('path', '/'), ('keeppackages', '0')]
        ]
        main()
        mock_print.assert_called_with(
            'There are encrypted filesystems: /dev/disk/by-label/foo, this may '
            'be an issue when migrating'
        )

    @patch('builtins.print')
    @patch('os.listdir')
    @patch('os.path.exists')
    def test_empty_repos(self, mock_os_exists, mock_os_listdir, mock_print):
        mock_os_exists.return_value = True
        mock_os_listdir.return_value = []
        check_remote_repos()
        mock_print.assert_called_with('No repositories in /etc/zypp/repos.d')
