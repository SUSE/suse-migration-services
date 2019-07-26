from unittest.mock import (
    patch, MagicMock
)
from pytest import raises
import io

from suse_migration_services.migration_config import MigrationConfig
from suse_migration_services.defaults import Defaults
from suse_migration_services.exceptions import (
    DistMigrationProductNotFoundException
)


class TestMigrationConfig(object):
    @patch.object(Defaults, 'get_migration_config_file')
    @patch.object(Defaults, 'get_system_migration_custom_config_file')
    def setup(
        self, mock_get_system_migration_config_custom_file,
        mock_get_migration_config_file
    ):
        mock_get_migration_config_file.return_value = \
            '../data/migration-config.yml'
        mock_get_system_migration_config_custom_file.return_value = \
            '../data/custom-migration-config.yml'
        self.config = MigrationConfig()

    def test_get_migration_product(self):
        assert self.config.get_migration_product() == 'SLES/15/x86_64'

    def test_get_preserve_udev_rules_list(self):
        assert self.config.get_preserve_udev_rules_list() == [
            '/etc/udev/rules.d/a.rules', '/etc/udev/rules.d/b.rules'
        ]

    @patch('suse_migration_services.logger.log.error')
    def test_get_migration_product_targets(self, mock_error):
        self.config.config_data = {'not_migration_product': 'another_info'}

        with raises(DistMigrationProductNotFoundException):
            self.config.get_migration_product()
            assert mock_error.called

    @patch.object(MigrationConfig, '_write_config_file')
    @patch('suse_migration_services.logger.log.info')
    def test_update_migration_config_file(
        self, mock_info, mock_write_config_file,
    ):
        self.config.update_migration_config_file()
        assert self.config.get_migration_product() == 'SLES/15.1/x86_64'
        assert self.config.is_debug_requested() is True
        assert mock_info.called

    def test_is_zypper_migration_plugin_requested(self):
        assert self.config.is_zypper_migration_plugin_requested() is True

    def test_is_debug_requested(self):
        assert self.config.is_debug_requested() is False

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

    @patch.object(Defaults, 'get_migration_config_file')
    @patch.object(Defaults, 'get_system_root_path')
    @patch.object(MigrationConfig, '_write_config_file')
    @patch('suse_migration_services.logger.log.info')
    def test_update_migration_config_file_detect_product(
        self, mock_info, mock_write_config_file, mock_get_system_root_path,
        mock_get_migration_config_file  # , mock_ElementTree
    ):
        mock_get_system_root_path.return_value = '../data/'
        mock_get_migration_config_file.return_value = \
            '../data/migration-config-detect-product.yml'
        self.config = MigrationConfig()
        self.config.update_migration_config_file()
        assert self.config.get_migration_product() == 'SLES_SAP/15.1/x86_64'
