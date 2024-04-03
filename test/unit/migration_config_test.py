from unittest.mock import (
    patch, MagicMock
)
from pytest import raises
import io
from collections import namedtuple

from suse_migration_services.migration_config import MigrationConfig
from suse_migration_services.suse_product import SUSEBaseProduct
from suse_migration_services.defaults import Defaults
from suse_migration_services.exceptions import (
    DistMigrationConfigDataException,
    DistMigrationProductNotFoundException
)


class TestMigrationConfig(object):
    @patch.object(Defaults, 'get_migration_config_file')
    @patch.object(Defaults, 'get_system_migration_custom_config_file')
    def setup_method(
        self, method, mock_get_system_migration_config_custom_file,
        mock_get_migration_config_file
    ):
        mock_get_migration_config_file.return_value = \
            '../data/migration-config.yml'
        mock_get_system_migration_config_custom_file.return_value = \
            '../data/custom-migration-config.yml'
        self.config = MigrationConfig()

    @patch.object(Defaults, 'get_os_release')
    @patch.object(Defaults, 'get_system_root_path')
    def test_get_migration_product_auto_detected(
        self, mock_get_system_root_path, mock_get_os_release
    ):
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
        mock_get_system_root_path.return_value = '../data'
        mock_get_os_release.return_value = os_release_result
        assert self.config.get_migration_product() == 'SLES/15.5/x86_64'

    @patch.object(Defaults, 'get_os_release')
    @patch.object(SUSEBaseProduct, 'get_tag')
    @patch.object(Defaults, 'get_system_root_path')
    def test_get_migration_product_targets(
        self, mock_get_system_root_path,
        mock_get_product_name, mock_get_os_release
    ):
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
        mock_get_system_root_path.return_value = '../data'
        mock_get_os_release.return_value = os_release_result
        mock_get_product_name.side_effect = Exception
        self.config.config_data = {'not_migration_product': 'another_info'}

        with raises(DistMigrationProductNotFoundException):
            self.config.get_migration_product()

    @patch.object(Defaults, 'get_os_release')
    @patch.object(SUSEBaseProduct, 'get_product_name')
    @patch.object(Defaults, 'get_system_root_path')
    @patch.object(MigrationConfig, '_write_config_file')
    def test_update_migration_config_file_no_autodetect(
        self, mock_write_config_file,
        mock_get_system_root_path, mock_get_product_name,
        mock_get_os_release
    ):
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
        mock_get_os_release.return_value = os_release_result
        mock_get_system_root_path.return_value = '../data'
        mock_get_product_name.return_value = None
        self.config.update_migration_config_file()
        assert self.config.get_migration_product() == 'SLES/15.5/x86_64'
        assert self.config.is_debug_requested() is True

    def test_is_zypper_migration_plugin_requested(self):
        assert self.config.is_zypper_migration_plugin_requested() is True

    def test_is_debug_requested(self):
        assert self.config.is_debug_requested() is False

    def test_is_host_independent_initd_requested(self):
        assert self.config.is_host_independent_initd_requested() is False

    def test_is_pre_checks_fix_requested(self):
        assert self.config.is_pre_checks_fix_requested() is True

    @patch('yaml.dump')
    def test_write_config_file(self, mock_yaml_dump):
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.config._write_config_file()
            mock_open.assert_called_once_with(
                self.config.migration_config_file, 'w'
            )
            mock_yaml_dump.assert_called_once_with(
                self.config.config_data, file_handle, default_flow_style=False
            )

    @patch.object(MigrationConfig, '_write_config_file')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch.object(Defaults, 'get_system_migration_custom_config_file')
    def test_update_migration_config_file_empty(
        self, mock_get_system_migration_config_custom_file,
        mock_get_migration_config_file,
        mock_write_config_file,
    ):
        mock_get_migration_config_file.return_value = \
            '../data/migration-config.yml'
        mock_get_system_migration_config_custom_file.return_value = \
            '../data/custom-migration-config-empty.yml'
        self.config = MigrationConfig()
        self.config.update_migration_config_file()

    @patch.object(MigrationConfig, '_write_config_file')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch.object(Defaults, 'get_system_migration_custom_config_file')
    def test_update_migration_config_file_just_comments(
        self, mock_get_system_migration_config_custom_file,
        mock_get_migration_config_file,
        mock_write_config_file,
    ):
        mock_get_migration_config_file.return_value = \
            '../data/migration-config.yml'
        mock_get_system_migration_config_custom_file.return_value = \
            '../data/custom-migration-config-just-comments.yml'
        self.config = MigrationConfig()
        self.config.update_migration_config_file()

    @patch.object(MigrationConfig, '_write_config_file')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch.object(Defaults, 'get_system_migration_custom_config_file')
    def test_update_migration_config_file_slightly_broken(
        self, mock_get_system_migration_config_custom_file,
        mock_get_migration_config_file, mock_write_config_file,
    ):
        mock_get_migration_config_file.return_value = \
            '../data/migration-config.yml'
        mock_get_system_migration_config_custom_file.return_value = \
            '../data/custom-migration-config-corrupt-string.yml'
        self.config = MigrationConfig()
        with raises(DistMigrationConfigDataException):
            self.config.update_migration_config_file()

    @patch.object(MigrationConfig, '_write_config_file')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch.object(Defaults, 'get_system_migration_custom_config_file')
    def test_update_migration_config_file_very_broken(
        self, mock_get_system_migration_config_custom_file,
        mock_get_migration_config_file, mock_write_config_file,
    ):
        mock_get_migration_config_file.return_value = \
            '../data/migration-config.yml'
        mock_get_system_migration_config_custom_file.return_value = \
            '../data/custom-migration-config-corrupt-mess.yml'
        self.config = MigrationConfig()
        with raises(DistMigrationConfigDataException):
            self.config.update_migration_config_file()

    @patch.object(MigrationConfig, '_write_config_file')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch.object(Defaults, 'get_system_migration_custom_config_file')
    def test_update_migration_config_file_violates_schema(
        self, mock_get_system_migration_config_custom_file,
        mock_get_migration_config_file, mock_write_config_file,
    ):
        mock_get_migration_config_file.return_value = \
            '../data/migration-config.yml'
        mock_get_system_migration_config_custom_file.return_value = \
            '../data/custom-migration-config-violates-schema.yml'
        self.config = MigrationConfig()
        with raises(DistMigrationConfigDataException):
            self.config.update_migration_config_file()

    @patch('yaml.dump')
    def test_get_migration_config_file_content(self, mock_yaml_dump):
        self.config.get_migration_config_file_content()
        mock_yaml_dump.assert_called_once_with(
            self.config.config_data, default_flow_style=False
        )
