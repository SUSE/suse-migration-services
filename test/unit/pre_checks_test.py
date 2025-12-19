import io
import argparse
import logging
import os
import subprocess
import yaml
from unittest.mock import (
    patch, call, Mock, MagicMock, mock_open
)
from pytest import fixture, mark

from suse_migration_services.command import Command
from suse_migration_services.fstab import Fstab
import suse_migration_services.prechecks.repos as check_repos
import suse_migration_services.prechecks.fs as check_fs
import suse_migration_services.prechecks.kernels as check_kernels
import suse_migration_services.prechecks.lsm as check_lsm
import suse_migration_services.prechecks.scc as check_scc
import suse_migration_services.prechecks.ha as check_ha
import suse_migration_services.prechecks.wicked2nm as check_wicked2nm
import suse_migration_services.prechecks.cpu_arch as check_cpu_arch
import suse_migration_services.prechecks.sshd as check_sshd
import suse_migration_services.prechecks.saptune as check_saptune
import suse_migration_services.prechecks.pre_checks as check_pre_checks
from suse_migration_services.exceptions import DistMigrationCommandException
from suse_migration_services.defaults import Defaults
from suse_migration_services.migration_target import MigrationTarget


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
    @patch('suse_migration_services.prechecks.cpu_arch.cpu_arch')
    @patch('suse_migration_services.prechecks.sshd.root_login')
    @patch.dict(
        os.environ, {"SUSE_MIGRATION_PRE_CHECKS_MODE": "foo"}, clear=True
    )
    @patch(
        'argparse.ArgumentParser.parse_args',
        return_value=argparse.Namespace(fix=False)
    )
    def test_main(
        self, mock_arg_parse, mock_sshd_root_login, mock_cpu_arch, mock_kernels,
        mock_fs, mock_repos, mock_os_geteuid, mock_log
    ):
        mock_os_geteuid.return_value = 0
        with self._caplog.at_level(logging.INFO):
            check_pre_checks.main()
            assert "Running suse-migration-pre-checks" in self._caplog.text

    @patch('suse_migration_services.prechecks.repos.remote_repos')
    @patch('suse_migration_services.prechecks.fs.encryption')
    @patch('suse_migration_services.prechecks.kernels.multiversion_and_multiple_kernels')
    @patch('suse_migration_services.prechecks.cpu_arch.cpu_arch')
    @patch('suse_migration_services.prechecks.sshd.root_login')
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
        self, mock_arg_parse, mock_sshd_root_login, mock_cpu_arch, mock_kernels, mock_fs,
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
    @patch('suse_migration_services.prechecks.cpu_arch.cpu_arch')
    @patch('suse_migration_services.prechecks.sshd.root_login')
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
        self, mock_argparse, mock_sshd_root_login, mock_cpu_arch, mock_kernels, mock_fs,
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

    @patch('os.path.exists')
    @patch.object(Command, 'run')
    @patch('builtins.open', new_callable=mock_open, read_data='Y')
    @patch('suse_migration_services.prechecks.lsm._apparmor_primitive_check')
    @patch('shutil.which')
    def test_check_lsm_migration(
        self, mock_shutil_which, mock_apparmor_primitive_check,
        mock_open, mock_Command_run, mock_os_path_exists,
        mock_os_geteuid, mock_log
    ):
        mock_shutil_which.return_value = True
        mock_os_path_exists.return_value = True

        aa_status_retval = Mock()
        aa_status_retval.output = '{"version": "2", "profiles": {"/usr/bin/lessopen.sh": "enforce", "apache2": "enforce", "apache2//DEFAULT_URI": "enforce", "apache2//HANDLING_UNTRUSTED_INPUT": "enforce", "apache2//phpsysinfo": "enforce", "avahi-daemon": "enforce", "dnsmasq": "enforce", "dnsmasq//libvirt_leaseshelper": "enforce", "docker-default": "enforce", "dovecot": "enforce", "dovecot-anvil": "enforce", "dovecot-auth": "enforce", "dovecot-config": "enforce", "dovecot-deliver": "enforce", "dovecot-dict": "enforce", "dovecot-director": "enforce", "dovecot-doveadm-server": "enforce", "dovecot-dovecot-auth": "enforce", "dovecot-dovecot-lda": "enforce", "dovecot-dovecot-lda//sendmail": "enforce", "dovecot-imap": "enforce", "dovecot-imap-login": "enforce", "dovecot-lmtp": "enforce", "dovecot-log": "enforce", "dovecot-managesieve": "enforce", "dovecot-managesieve-login": "enforce", "dovecot-pop3": "enforce", "dovecot-pop3-login": "enforce", "dovecot-replicator": "enforce", "dovecot-script-login": "enforce", "dovecot-ssl-params": "enforce", "dovecot-stats": "enforce", "identd": "enforce", "klogd": "enforce", "lsb_release": "enforce", "mdnsd": "enforce", "nmbd": "enforce", "nscd": "enforce", "ntpd": "enforce", "nvidia_modprobe": "enforce", "nvidia_modprobe//kmod": "enforce", "php-fpm": "enforce", "ping": "enforce", "samba-bgqd": "enforce", "samba-dcerpcd": "enforce", "samba-rpcd": "enforce", "samba-rpcd-classic": "enforce", "samba-rpcd-spoolss": "enforce", "smbd": "enforce", "smbldap-useradd": "enforce", "smbldap-useradd///etc/init.d/nscd": "enforce", "syslog-ng": "enforce", "syslogd": "enforce", "traceroute": "enforce", "unix-chkpwd": "enforce", "winbindd": "enforce", "zgrep": "enforce", "zgrep//helper": "enforce", "zgrep//sed": "enforce"}, "processes": {"/usr/sbin/nscd": [{"profile": "nscd", "pid": "783", "status": "enforce"}]}}'

        rpm_verify_retval = Mock()
        rpm_verify_retval.output = 'S.5....T.  c /some/path\nS.5....T.  c /etc/apparmor.d/some_file'

        def command_run_retval(array, raise_on_error=False):
            if array[0] == 'aa-status':
                return aa_status_retval
            elif array[0] == 'rpm':
                return rpm_verify_retval

        mock_Command_run.side_effect = command_run_retval
        mock_apparmor_primitive_check.return_value = False
        with self._caplog.at_level(logging.ERROR):
            check_lsm.check_lsm(migration_system=False)
            assert 'Modified AppArmor profiles found' \
                in self._caplog.text
            assert 'please verify changes to the files from: "rpm -V apparmor-profiles"' \
                in self._caplog.text
            assert 'Non-default AppArmor setup detected' \
                in self._caplog.text
            assert 'please review the details above' \
                in self._caplog.text
        mock_Command_run.assert_called()

    @patch.object(Command, 'run')
    @patch('suse_migration_services.prechecks.lsm._apparmor_enabled')
    @patch('shutil.which')
    def test_check_lsm_migration_failed(
        self, mock_shutil_which, mock_apparmor_enabled, mock_Command_run,
        mock_os_geteuid, mock_log
    ):
        mock_shutil_which.return_value = True
        mock_apparmor_enabled.return_value = True
        mock_Command_run.side_effect = Exception
        with self._caplog.at_level(logging.WARNING):
            check_lsm.check_lsm(migration_system=False)
            assert 'aa-status failed with' in self._caplog.text
            assert 'Skipping LSM checks' in self._caplog.text

    @patch('os.path.exists')
    @patch.object(Command, 'run')
    @patch('shutil.which')
    def test_check_lsm_migration_simple(
        self, mock_shutil_which, mock_Command_run, mock_os_path_exists,
        mock_os_geteuid, mock_log
    ):
        mock_shutil_which.return_value = False
        find_retval = Mock()
        find_retval.output = Mock()
        find_retval.output.count = Mock()
        find_retval.output.count.return_value = 300

        mock_Command_run.return_value = find_retval

        with patch('builtins.open', new_callable=mock_open, read_data='Y'):
            with self._caplog.at_level(logging.INFO):
                check_lsm.check_lsm(migration_system=False)
                assert 'please install "apparmor-parser" as aa-status' in \
                    self._caplog.text

    @patch('suse_migration_services.prechecks.lsm._apparmor_enabled')
    def test_check_lsm_migration_apparmor_disabled(
        self, mock_apparmor_enabled, mock_os_geteuid, mock_log
    ):
        mock_apparmor_enabled.return_value = False
        with self._caplog.at_level(logging.INFO):
            check_lsm.check_lsm(migration_system=False)
            assert 'AppArmor disabled' in self._caplog.text

    @patch('yaml.safe_load')
    @patch('glob.glob')
    @patch('os.path.isfile')
    @patch('requests.post')
    @patch.object(Command, 'run')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch.object(MigrationTarget, 'get_migration_target')
    def test_check_scc_migration(
        self, mock_get_migration_target, mock_get_migration_config_file,
        mock_Command_run, mock_requests_post,
        mock_os_path_isfile, mock_glob, mock_yaml_safe_load,
        mock_os_geteuid, mock_log
    ):
        mock_get_migration_target.return_value = {
            'identifier': 'SLES',
            'version': '15.3',
            'arch': 'x86_64'
        }
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

            # Test exception on get_migration_target
            mock_get_migration_target.return_value = {}
            check_scc.migration()
            assert not mock_requests_post.called

    @patch('sys.exit')
    def test_privileges(self, mock_sys_exit, mock_os_geteuid, mock_log):
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

    @patch.object(Command, 'run')
    def test_check_wicked2nm_not_running_during_migration(
        self, mock_Command_run, mock_os_geteuid, mock_log
    ):
        check_wicked2nm.check_wicked2nm(migration_system=True)
        assert not mock_Command_run.called

    @patch('shutil.which')
    @patch.object(Command, 'run')
    def test_check_wicked2nm_no_wicked(
        self, mock_Command_run, mock_shutil_which,
        mock_os_geteuid, mock_log
    ):
        mock_shutil_which.return_value = False
        check_wicked2nm.check_wicked2nm(migration_system=True)
        assert not mock_Command_run.called
        check_wicked2nm.check_wicked2nm(migration_system=False)
        assert not mock_Command_run.called

    @patch('shutil.which')
    @patch('os.path.isfile')
    @patch('suse_migration_services.prechecks.wicked2nm.NamedTemporaryFile')
    @patch('suse_migration_services.prechecks.wicked2nm.Command.run')
    def test_check_wicked2nm_no_cached_config(
        self, mock_Command_run, mock_NamedTemporaryFile,
        mock_os_path_isfile, mock_shutil_which,
        mock_os_geteuid, mock_log
    ):
        tempfile = Mock()
        tempfile.name = 'tmpfile'
        mock_NamedTemporaryFile.return_value = tempfile
        wicked2nm_result = Mock()
        wicked2nm_result.output = 'some wicked config'
        wicked2nm_result.error = '[WARN] Unhandled field\n[ERROR] some'
        wicked2nm_result.returncode = 3
        mock_Command_run.return_value = wicked2nm_result
        mock_shutil_which.return_value = 'some'
        mock_os_path_isfile.return_value = False
        with patch('builtins.open', create=True):
            with self._caplog.at_level(logging.WARNING):
                check_wicked2nm.check_wicked2nm(migration_system=False)
                mock_NamedTemporaryFile.assert_called_once_with()
                assert mock_Command_run.call_args_list == [
                    call(
                        ['wicked', 'show-config']
                    ),
                    call(
                        [
                            'wicked2nm', 'migrate',
                            '--disable-hints', '--dry-run',
                            'tmpfile'
                        ],
                        raise_on_error=False
                    )
                ]
                assert 'wicked2nm detected potential migration issues' in \
                    self._caplog.text

    @patch('shutil.which')
    @patch('os.path.isfile')
    @patch('suse_migration_services.prechecks.wicked2nm.Command.run')
    def test_check_wicked2nm_has_config(
        self, mock_Command_run, mock_os_path_isfile, mock_shutil_which,
        mock_os_geteuid, mock_log
    ):
        wicked2nm_result = Mock()
        wicked2nm_result.error = '[WARN] Unhandled field\n[ERROR] some'
        wicked2nm_result.returncode = 1
        mock_Command_run.return_value = wicked2nm_result
        mock_shutil_which.return_value = 'some'
        mock_os_path_isfile.return_value = True
        with self._caplog.at_level(logging.ERROR):
            check_wicked2nm.check_wicked2nm(migration_system=False)
            mock_Command_run.assert_called_once_with(
                [
                    'wicked2nm', 'migrate',
                    '--disable-hints', '--dry-run',
                    '--netconfig-base-dir', '/etc/sysconfig/network',
                    '/var/cache/wicked_config/config.xml'
                ], raise_on_error=False
            )
            assert 'wicked2nm cannot migrate the network setup:' in \
                self._caplog.text
        wicked2nm_result.returncode = 0
        with self._caplog.at_level(logging.INFO):
            check_wicked2nm.check_wicked2nm(migration_system=False)
            assert 'wicked2nm can migrate the network setup' in \
                self._caplog.text

    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.migration_target.MigrationTarget.get_migration_target')
    def test_check_x86_64_v2(
            self, mock_get_migration_target, mock_Command_run,
            mock_os_getuid, mock_log
    ):
        mock_get_migration_target.return_value = {
            'version': '16.0'
        }
        mock_Command_run.return_value.output = 'x86_64_v2'

        check_cpu_arch.cpu_arch()
        assert 'SLE16 requires x86_64_v2 at minimum' not in self._caplog.text
        mock_Command_run.assert_called_once_with(['zypper', 'system-architecture'])

    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.migration_target.MigrationTarget.get_migration_target')
    def test_check_x86_64_v1(
            self, mock_get_migration_target, mock_Command_run,
            mock_os_getuid, mock_log
    ):
        mock_get_migration_target.return_value = {
            'version': '16.0'
        }
        mock_Command_run.return_value.output = 'x86_64'

        with self._caplog.at_level(logging.ERROR):
            check_cpu_arch.cpu_arch()
            assert 'SLE16 requires x86_64_v2 at minimum' in self._caplog.text
        mock_Command_run.assert_called_once_with(['zypper', 'system-architecture'])

    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.migration_target.MigrationTarget.get_migration_target')
    def test_check_x86_64_v1_sle15(
            self, mock_get_migration_target, mock_Command_run,
            mock_os_getuid, mock_log
    ):
        mock_get_migration_target.return_value = {
            'version': '15.0'
        }
        mock_Command_run.return_value.output = 'x86_64'

        with self._caplog.at_level(logging.ERROR):
            check_cpu_arch.cpu_arch()
            assert 'SLE16 requires x86_64_v2 at minimum' not in self._caplog.text
        mock_Command_run.assert_not_called()

    @patch('suse_migration_services.command.Command.run')
    @patch.object(MigrationTarget, 'get_migration_target')
    def test_check_sshd_root_login_disabled(
        self,
        mock_get_migration_target,
        mock_Command_run,
        mock_os_getuid,
        mock_log
    ):
        mock_get_migration_target.return_value = {'version': '16.0'}
        mock_Command_run.return_value.returncode = 1
        with self._caplog.at_level(logging.WARNING):
            check_sshd.root_login(migration_system=False)
            assert 'Root login by ssh will be disabled' not in self._caplog.text
        mock_Command_run.assert_called_once_with(
            ['systemctl', '--quiet', 'is-enabled', 'sshd'],
            raise_on_error=False
        )

    @patch('suse_migration_services.command.Command.run')
    @patch.object(MigrationTarget, 'get_migration_target')
    def test_check_sshd_root_login_yes(
        self,
        mock_get_migration_target,
        mock_Command_run,
        mock_os_getuid,
        mock_log
    ):
        mock_get_migration_target.return_value = {'version': '16.0'}
        mock_systemctl_run = Mock()
        mock_systemctl_run.returncode = 0
        mock_sshd_run = Mock()
        mock_sshd_run.output = 'permitrootlogin yes\n'
        mock_Command_run.side_effect = [mock_systemctl_run, mock_sshd_run]
        with self._caplog.at_level(logging.WARNING):
            check_sshd.root_login(migration_system=False)
            assert 'Root login by ssh will be disabled ' in self._caplog.text
        mock_Command_run.assert_has_calls(
            [
                call(
                    ['systemctl', '--quiet', 'is-enabled', 'sshd'],
                    raise_on_error=False
                ),
                call(['sshd', '-T'])
            ]
        )

    @patch('suse_migration_services.command.Command.run')
    @patch.object(MigrationTarget, 'get_migration_target')
    def test_check_sshd_root_login_no(
        self,
        mock_get_migration_target,
        mock_Command_run,
        mock_os_getuid,
        mock_log
    ):
        mock_get_migration_target.return_value = {'version': '16.0'}
        mock_systemctl_run = Mock()
        mock_systemctl_run.returncode = 0
        mock_sshd_run = Mock()
        mock_sshd_run.output = 'permitrootlogin no\n'
        mock_Command_run.side_effect = [mock_systemctl_run, mock_sshd_run]

        with self._caplog.at_level(logging.WARNING):
            check_sshd.root_login(migration_system=False)
            assert 'Root login by ssh will be disabled' not in self._caplog.text
        mock_Command_run.assert_has_calls(
            [
                call(
                    ['systemctl', '--quiet', 'is-enabled', 'sshd'],
                    raise_on_error=False
                ),
                call(['sshd', '-T'])
            ]
        )

    @patch('suse_migration_services.command.Command.run')
    def test_check_sshd_root_login_in_migration_system(
        self,
        mock_Command_run,
        mock_os_getuid,
        mock_log
    ):
        check_sshd.root_login(migration_system=True)
        mock_Command_run.assert_not_called()

    @patch('suse_migration_services.command.Command.run')
    @patch.object(MigrationTarget, 'get_migration_target')
    def test_check_sshd_root_login_old_sles(
        self,
        mock_get_migration_target,
        mock_Command_run,
        mock_os_getuid,
        mock_log
    ):
        mock_get_migration_target.return_value = {'version': '15.7'}
        check_sshd.root_login(migration_system=False)
        mock_Command_run.assert_not_called()

    @patch('suse_migration_services.command.Command.run')
    def test__get_service_enabled_state(self, mock_Command_run,
                                        mock_os_getuid, mock_log):
        mock = Mock()
        mock_Command_run.return_value = mock
        for state in ['not-found', 'enabled', 'disabled']:
            mock.output = state
            assert check_saptune._get_service_enabled_state('foobar.service') == state
            mock_Command_run.assert_called_with(['systemctl', 'is-enabled', 'foobar.service'])
        mock.output = 'not-found'
        assert check_saptune._get_service_enabled_state('foobar.service', '/foobar') == 'not-found'
        mock_Command_run.assert_called_with(['systemctl', '--root', '/foobar', 'is-enabled', 'foobar.service'])

    @patch('builtins.open')
    def test__write_marker(self, mock_open, mock_os_getuid, mock_log):
        with self._caplog.at_level(logging.CRITICAL):
            result = check_saptune._write_marker('foobar', '/root')
            assert result == True
            assert self._caplog.text == ''
        mock_open.return_value.__enter__.return_value.write.assert_called_once_with('foobar')
        mock_open.assert_called_with('/root/var/tmp/migration-saptune', 'w')
        
        mock_open.side_effect = IOError()
        with self._caplog.at_level(logging.CRITICAL):
            result = check_saptune._write_marker('foobar')
            assert result == False
            assert 'Could not write migration marker. Tuning is not as expected after migration!' in self._caplog.text
        mock_open.return_value.__enter__.return_value.write.assert_called_once_with('foobar')
        mock_open.assert_called_with('/var/tmp/migration-saptune', 'w')

    @patch('suse_migration_services.prechecks.saptune._get_os')
    @patch('suse_migration_services.prechecks.saptune._get_installed_patterns')
    def test_check_saptune_os(self, mock_get_installed_patterns, mock_get_os,
                              mock_os_getuid, mock_log):
        mock_get_installed_patterns.return_value = []

        for retval in ['SLES', 'SLES_SAP', None]:
            mock_get_os.return_value = retval
            with self._caplog.at_level(logging.WARNING):
                check_saptune.check_saptune()
                if not retval:
                    assert "Could not determine OS!" in self._caplog.text

    @patch('suse_migration_services.prechecks.saptune._get_os')
    @patch('suse_migration_services.prechecks.saptune._get_installed_patterns')
    def test_check_saptune_installed_patterns(self, mock_get_installed_patterns, 
                                              mock_get_os, mock_os_getuid, mock_log):
        mock_get_os.return_value = 'SLES'

        for retval in [['base'], []]:
            mock_get_installed_patterns.return_value = retval
            with self._caplog.at_level(logging.WARNING):
                check_saptune.check_saptune()
                if not retval:
                    assert "Could not get installed patterns!" in self._caplog.text

    @staticmethod
    def _test_data_generator(datafile):
        with open(datafile, 'r') as f:
            for dataset in yaml.safe_load(f):
                yield dataset

    @patch('suse_migration_services.prechecks.saptune._get_os')
    @patch('suse_migration_services.prechecks.saptune._get_installed_patterns')
    @patch('suse_migration_services.prechecks.saptune._get_service_enabled_state')
    @patch('suse_migration_services.prechecks.saptune._write_marker')
    @mark.parametrize("os_name, patterns, saptune_state, sapconf_state, marker_content, valid", 
                      _test_data_generator('../data/saptune_test_data.yaml'))
    def test_check_saptune_sapconf_saptune(self, mock_write_marker,
                                           mock_get_service_enabled_state,
                                           mock_get_installed_patterns,
                                           mock_get_os, mock_os_getuid, mock_log,
                                           os_name, patterns, saptune_state, 
                                           sapconf_state, marker_content, valid):
        mock_get_os.return_value = os_name
        mock_get_installed_patterns.return_value = patterns
        mock_get_service_enabled_state.side_effect = [sapconf_state, saptune_state]

        with self._caplog.at_level(logging.INFO):
            check_saptune.check_saptune(migration_system=True)
            if marker_content:
                assert f'Marker content: {marker_content}' in self._caplog.text
                assert f'Unknown configuration' not in self._caplog.text
                mock_write_marker.assert_called_with(marker_content, path_prefix='/system-root')
            else:
                assert f'Marker content:' not in self._caplog.text
                if valid:
                    assert f'Unknown configuration' not in self._caplog.text
                else:
                    assert f'Unknown configuration' in self._caplog.text
