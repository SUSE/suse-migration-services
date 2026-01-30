from unittest.mock import patch, MagicMock
from pytest import raises, fixture
import logging
import io
import os
import yaml
from collections import namedtuple

from suse_migration_services.defaults import Defaults


class TestDefaults(object):
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup_method(self):
        self.defaults = Defaults()

    def test_get_migration_config_file(self):
        assert self.defaults.get_migration_config_file() == '/etc/migration-config.yml'

    def test_get_grub_default_file(self):
        assert self.defaults.get_grub_default_file() == '/system-root/etc/default/grub'

    def test_get_target_kernel(self):
        with patch('platform.machine') as mock_platform_machine:
            mock_platform_machine.return_value = 'x86_64'
            assert self.defaults.get_target_kernel() == 'boot/vmlinuz'
            mock_platform_machine.return_value = 'aarch64'
            assert self.defaults.get_target_kernel() == 'boot/Image'
            mock_platform_machine.return_value = 'ppc64le'
            assert self.defaults.get_target_kernel() == 'boot/vmlinux'
            mock_platform_machine.return_value = 's390x'
            assert self.defaults.get_target_kernel() == 'boot/image'
            mock_platform_machine.return_value = 'unknown_platform'
            with raises(NotImplementedError):
                self.defaults.get_target_kernel()

    def test_get_os_release(self):
        os_release_tuple = namedtuple(
            'OSRelease',
            [
                'name',
                'version',
                'version_id',
                'pretty_name',
                'id',
                'id_like',
                'ansi_color',
                'cpe_name',
            ],
        )
        os_release_result = os_release_tuple(
            name='SLES',
            version='15-SP3',
            version_id='15.3',
            pretty_name='SUSE Linux Enterprise Server 15 SP3',
            id='sles',
            id_like='suse',
            ansi_color='0;32',
            cpe_name='cpe:/o:suse:sles:15:sp3',
        )
        os_release_content = (
            'NAME="SLES"\n'
            'VERSION="15-SP3"\n'
            'VERSION_ID="15.3"\n'
            'PRETTY_NAME="SUSE Linux Enterprise Server 15 SP3"\n'
            'ID="sles"\n'
            'ID_LIKE="suse"\n'
            'ANSI_COLOR="0;32"\n'
            'CPE_NAME="cpe:/o:suse:sles:15:sp3"'
        )
        with patch('builtins.open', create=True) as mock_open:
            mock_open_os_release = MagicMock(spec=io.IOBase)

            def open_file(filename, mode):
                if filename == '/etc/os-release':
                    return mock_open_os_release.return_value

            mock_open.side_effect = open_file
            file_handle = mock_open_os_release.return_value.__enter__.return_value
            file_handle.read.return_value = os_release_content
            assert self.defaults.get_os_release() == os_release_result

    def test_get_os_release_with_comments_and_blanks(self):
        os_release_content = (
            'NAME="openSUSE Tumbleweed"\n'
            '# VERSION="20250505"\n'
            '\n'
            'ID="opensuse-tumbleweed"\n'
            'ID_LIKE=opensuse suse\n'  # Value not in quotes
            'VERSION_ID="20250505"\n'
            '#PRETTY_NAME="openSUSE Tumbleweed"\n'
            '  # ANSI_COLOR="0;32" with leading space comment\n'
            'MALFORMED_LINE_NO_EQUALS\n'  # This line will be skipped
        )
        # Expected order of fields based on valid lines in os_release_content
        ordered_os_release_tuple = namedtuple('OSRelease', ['name', 'id', 'id_like', 'version_id'])
        expected_result = ordered_os_release_tuple(
            name='openSUSE Tumbleweed',
            id='opensuse-tumbleweed',
            id_like='opensuse suse',
            version_id='20250505',
        )

        with patch('builtins.open', create=True) as mock_open:
            mock_open_os_release = MagicMock(spec=io.IOBase)

            def open_file(filename, mode):
                if filename == '/etc/os-release':
                    return mock_open_os_release.return_value
                # Fallback for other open calls if any,
                # though not expected here
                return MagicMock(spec=io.IOBase)

            mock_open.side_effect = open_file
            file_handle = mock_open_os_release.return_value.__enter__.return_value
            file_handle.read.return_value = os_release_content
            parsed_result = self.defaults.get_os_release()
            assert parsed_result == expected_result
            assert parsed_result._fields == ('name', 'id', 'id_like', 'version_id')

    def test_get_os_release_empty_file(self):
        os_release_content = ""
        expected_empty_tuple = namedtuple('OSRelease', [])()
        with patch('builtins.open', create=True) as mock_open:
            mock_open_os_release = MagicMock(spec=io.IOBase)

            def open_file(filename, mode):
                if filename == '/etc/os-release':
                    return mock_open_os_release.return_value
                return MagicMock(spec=io.IOBase)

            mock_open.side_effect = open_file
            file_handle = mock_open_os_release.return_value.__enter__.return_value
            file_handle.read.return_value = os_release_content
            assert self.defaults.get_os_release() == expected_empty_tuple

    def test_get_os_release_only_comments(self):
        os_release_content = "# This is a comment\n# Another comment"
        expected_empty_tuple = namedtuple('OSRelease', [])()
        with patch('builtins.open', create=True) as mock_open:
            mock_open_os_release = MagicMock(spec=io.IOBase)

            def open_file(filename, mode):
                if filename == '/etc/os-release':
                    return mock_open_os_release.return_value
                return MagicMock(spec=io.IOBase)

            mock_open.side_effect = open_file
            file_handle = mock_open_os_release.return_value.__enter__.return_value
            file_handle.read.return_value = os_release_content
            assert self.defaults.get_os_release() == expected_empty_tuple

    def test_get_proxy_path(self):
        assert self.defaults.get_proxy_path() == '/etc/sysconfig/proxy'

    @patch.dict(os.environ, {'foo': 'bar', 'a': 'b'}, clear=True)
    def test_log_env(self):
        log = logging.getLogger('foo')
        with self._caplog.at_level(logging.INFO):
            self.defaults.log_env(log)
        assert ' Env variables' in self._caplog.text
        assert ' a: b\nfoo: bar\n\n' in self._caplog.text

    @patch.object(Defaults, 'get_proxy_path')
    @patch('suse_migration_services.defaults.os')
    def test_update_env(self, mock_os, mock_proxy_path):
        with open('../data/migration-config-proxy.yml', 'r') as config:
            config_data = yaml.safe_load(config)
        mock_os.linesep = '\n'
        mock_proxy_path.return_value = '../data/etc/sysconfig/proxy'
        self.defaults.update_env(config_data.get('preserve'))
        mock_os.environ.update.assert_called_once_with({'http_foo': 'bar'})
