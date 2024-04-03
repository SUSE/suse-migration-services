from unittest.mock import (
    patch, MagicMock
)
import io
from collections import namedtuple

from suse_migration_services.defaults import Defaults


class TestDefaults(object):
    def setup_method(self):
        self.defaults = Defaults()

    def test_get_migration_config_file(self):
        assert self.defaults.get_migration_config_file() == \
            '/etc/migration-config.yml'

    def test_get_os_release(self):
        os_release_tuple = namedtuple(
            'OSRelease', [
                'name', 'version', 'version_id',
                'pretty_name', 'id', 'id_like', 'ansi_color', 'cpe_name'
            ]
        )
        os_release_result = os_release_tuple(
            name='SLES', version='15-SP5', version_id='15.5',
            pretty_name='SUSE Linux Enterprise Server 15 SP5',
            id='sles', id_like='suse', ansi_color='0;32',
            cpe_name='cpe:/o:suse:sles:15:sp5'
        )
        os_release_content = ('NAME="SLES"\n'
                              'VERSION="15-SP5"\n'
                              'VERSION_ID="15.5"\n'
                              'PRETTY_NAME="SUSE Linux Enterprise Server 15 SP5"\n'
                              'ID="sles"\n'
                              'ID_LIKE="suse"\n'
                              'ANSI_COLOR="0;32"\n'
                              'CPE_NAME="cpe:/o:suse:sles:15:sp5"')
        with patch('builtins.open', create=True) as mock_open:
            mock_open_os_release = MagicMock(spec=io.IOBase)

            def open_file(filename, mode):
                if filename == '/etc/os-release':
                    return mock_open_os_release.return_value

            mock_open.side_effect = open_file
            file_handle = \
                mock_open_os_release.return_value.__enter__.return_value
            file_handle.read.return_value = os_release_content
            assert self.defaults.get_os_release() == os_release_result

    def test_get_proxy_path(self):
        assert self.defaults.get_proxy_path() == \
            '/etc/sysconfig/proxy'
