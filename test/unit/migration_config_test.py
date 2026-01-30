from unittest.mock import patch, MagicMock, call
from pytest import raises
import io
from copy import deepcopy
from collections import namedtuple

from suse_migration_services.migration_config import MigrationConfig
from suse_migration_services.suse_product import SUSEBaseProduct
from suse_migration_services.defaults import Defaults
from suse_migration_services.exceptions import (
    DistMigrationConfigDataException,
    DistMigrationProductNotFoundException,
)


class TestMigrationConfig(object):
    @patch.object(Defaults, 'get_migration_config_dir')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch.object(Defaults, 'get_system_migration_custom_config_file')
    def setup_method(
        self,
        method,
        mock_get_system_migration_config_custom_file,
        mock_get_migration_config_file,
        mock_get_migration_config_dir,
    ):
        mock_get_migration_config_dir.return_value = '../data/migration-config.d'
        mock_get_migration_config_file.return_value = '../data/migration-config.yml'
        mock_get_system_migration_config_custom_file.return_value = (
            '../data/custom-migration-config.yml'
        )
        self.config = MigrationConfig()

    @patch.object(Defaults, 'get_os_release')
    @patch.object(Defaults, 'get_system_root_path')
    def test_get_migration_product_auto_detected(
        self, mock_get_system_root_path, mock_get_os_release
    ):
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
        mock_get_system_root_path.return_value = '../data'
        mock_get_os_release.return_value = os_release_result
        assert self.config.get_migration_product() == 'SLES/15.3/x86_64'

    @patch.object(Defaults, 'get_os_release')
    @patch.object(SUSEBaseProduct, 'get_tag')
    @patch.object(Defaults, 'get_system_root_path')
    def test_get_migration_product_targets(
        self, mock_get_system_root_path, mock_get_product_name, mock_get_os_release
    ):
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
        self,
        mock_write_config_file,
        mock_get_system_root_path,
        mock_get_product_name,
        mock_get_os_release,
    ):
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
        mock_get_os_release.return_value = os_release_result
        mock_get_system_root_path.return_value = '../data'
        mock_get_product_name.return_value = None
        self.config.update_migration_config_file()
        assert self.config.get_migration_product() == 'SLES/15.3/x86_64'
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
            mock_open.assert_called_once_with(self.config.migration_config_file, 'w')
            mock_yaml_dump.assert_called_once_with(
                self.config.config_data, file_handle, default_flow_style=False
            )

    @patch.object(MigrationConfig, '_write_config_file')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch.object(Defaults, 'get_system_migration_custom_config_file')
    def test_update_migration_config_file_empty(
        self,
        mock_get_system_migration_config_custom_file,
        mock_get_migration_config_file,
        mock_write_config_file,
    ):
        mock_get_migration_config_file.return_value = '../data/migration-config.yml'
        mock_get_system_migration_config_custom_file.return_value = (
            '../data/custom-migration-config-empty.yml'
        )
        self.config = MigrationConfig()
        self.config.update_migration_config_file()

    @patch.object(MigrationConfig, '_write_config_file')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch.object(Defaults, 'get_system_migration_custom_config_file')
    def test_update_migration_config_file_just_comments(
        self,
        mock_get_system_migration_config_custom_file,
        mock_get_migration_config_file,
        mock_write_config_file,
    ):
        mock_get_migration_config_file.return_value = '../data/migration-config.yml'
        mock_get_system_migration_config_custom_file.return_value = (
            '../data/custom-migration-config-just-comments.yml'
        )
        self.config = MigrationConfig()
        self.config.update_migration_config_file()

    @patch.object(MigrationConfig, '_write_config_file')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch.object(Defaults, 'get_system_migration_custom_config_file')
    def test_update_migration_config_file_slightly_broken(
        self,
        mock_get_system_migration_config_custom_file,
        mock_get_migration_config_file,
        mock_write_config_file,
    ):
        mock_get_migration_config_file.return_value = '../data/migration-config.yml'
        mock_get_system_migration_config_custom_file.return_value = (
            '../data/custom-migration-config-corrupt-string.yml'
        )
        self.config = MigrationConfig()
        with raises(DistMigrationConfigDataException):
            self.config.update_migration_config_file()

    @patch.object(MigrationConfig, '_write_config_file')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch.object(Defaults, 'get_system_migration_custom_config_file')
    def test_update_migration_config_file_very_broken(
        self,
        mock_get_system_migration_config_custom_file,
        mock_get_migration_config_file,
        mock_write_config_file,
    ):
        mock_get_migration_config_file.return_value = '../data/migration-config.yml'
        mock_get_system_migration_config_custom_file.return_value = (
            '../data/custom-migration-config-corrupt-mess.yml'
        )
        self.config = MigrationConfig()
        with raises(DistMigrationConfigDataException):
            self.config.update_migration_config_file()

    @patch.object(MigrationConfig, '_write_config_file')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch.object(Defaults, 'get_system_migration_custom_config_file')
    def test_update_migration_config_file_violates_schema(
        self,
        mock_get_system_migration_config_custom_file,
        mock_get_migration_config_file,
        mock_write_config_file,
    ):
        mock_get_migration_config_file.return_value = '../data/migration-config.yml'
        mock_get_system_migration_config_custom_file.return_value = (
            '../data/custom-migration-config-violates-schema.yml'
        )
        self.config = MigrationConfig()
        with raises(DistMigrationConfigDataException):
            self.config.update_migration_config_file()

    @patch('yaml.dump')
    def test_get_migration_config_file_content(self, mock_yaml_dump):
        self.config.get_migration_config_file_content()
        mock_yaml_dump.assert_called_once_with(self.config.config_data, default_flow_style=False)

    @patch.object(Defaults, 'get_migration_config_dir')
    @patch.object(Defaults, 'get_migration_config_file')
    def test_get_migration_missing_dropin_dir(
        self, mock_get_migration_config_file, mock_get_migration_config_dir
    ):
        mock_get_migration_config_dir.return_value = '../data/DOES_NOT_EXISTS'
        mock_get_migration_config_file.return_value = '../data/migration-config.yml'
        self.config = MigrationConfig()

    @patch.object(MigrationConfig, '_write_config_file')
    @patch.object(Defaults, 'get_system_migration_custom_config_file')
    @patch.object(MigrationConfig, '_parse_config_file')
    @patch.object(Defaults, 'get_migration_config_dir')
    @patch.object(Defaults, 'get_migration_config_file')
    def test_get_migration_config_merge_file_order(
        self,
        mock_get_migration_config_file,
        mock_get_migration_config_dir,
        mock_parse_config_file,
        mock_get_system_migration_config_custom_file,
        mock_write_config_file,
    ):
        mock_get_migration_config_dir.return_value = '../data/migration-config.d'
        mock_get_migration_config_file.return_value = '../data/migration-config.yml'
        mock_get_system_migration_config_custom_file.return_value = (
            '../data/custom-migration-config.yml'
        )

        self.config = MigrationConfig()
        self.config.update_migration_config_file()

        assert mock_parse_config_file.call_args_list == [
            call('../data/migration-config.yml'),
            call('../data/migration-config.d/10-enable-wicked2nm-continue-migration.yml'),
            call('../data/migration-config.d/10-s390.yml'),
            call('../data/migration-config.d/20-migration-config-duplicates.yml'),
            call('../data/migration-config.d/50-disable-wicked2nm-continue-migration.yml'),
            call('../data/custom-migration-config.yml'),
        ]

    @patch.object(MigrationConfig, '_write_config_file')
    @patch.object(Defaults, 'get_system_migration_custom_config_file')
    @patch.object(Defaults, 'get_migration_config_dir')
    @patch.object(Defaults, 'get_migration_config_file')
    def test_get_migration_config_merge(
        self,
        mock_get_migration_config_file,
        mock_get_migration_config_dir,
        mock_get_system_migration_config_custom_file,
        mock_write_config_file,
    ):
        mock_get_migration_config_dir.return_value = '../data/migration-config.d'
        mock_get_migration_config_file.return_value = '../data/migration-config.yml'
        mock_get_system_migration_config_custom_file.return_value = (
            '../data/custom-migration-config.yml'
        )

        self.config = MigrationConfig()
        self.config.update_migration_config_file()

        # Check values get successful overwritten in correct order
        assert (
            self.config.config_data.get('network', {}).get('wicked2nm-continue-migration') is False
        )
        # Check list get appended without including duplicates
        preserve = self.config.config_data.get('preserve', {})
        assert preserve.get('rules', []) == [
            '/etc/udev/rules.d/*.rules',
            '/etc/udev/rules.d/*qeth*.rules',
            '/etc/udev/rules.d/*-cio-ignore*.rules',
        ]
        assert preserve.get('sysctl', []) == ['/etc/sysctl.conf']
        assert preserve.get('static', []) == ['/etc/sysconfig/proxy']

        # Changes from custom-migration-config.yml
        assert self.config.is_debug_requested()
        assert self.config.get_migration_product() == "SLES/15.3/x86_64"

        # Check no other key's exists
        assert list(self.config.config_data.keys()) == [
            'preserve',
            'network',
            'debug',
            'migration_product',
        ]

    def test_merge_config_dicts(self):
        dictA = {
            'key1': 'dictA.key1',
            'key2': ['dictA.key2-1', 'dictA.key2-2'],
            'key3': {
                'key3.1': 'dictA.key3.1',
                'key3.2': ['dictA.key3.2-1', 'dictA.key3.2-2'],
                'key3.3': 'dictA.key3.3',
            },
            'key4': 'dictA.key4',
        }
        dictA_copy = deepcopy(dictA)

        dictB = {
            'key2': ['dictB.key2-1', 'dictB.key2-2'],
            'key3': {
                'key3.2': ['dictB.key3.2-1', 'dictB.key3.2-2'],
                'key3.3': 'dictB.key3.3',
                'key3.4': 'dictB.key3.4',
            },
            'key4': 'dictB.key4',
            'key5': 'dictB.key5',
        }
        MigrationConfig._merge_config_dicts(dictA, {})
        assert dictA == dictA_copy

        empty = {}
        MigrationConfig._merge_config_dicts(empty, dictA)
        assert empty == dictA_copy

        MigrationConfig._merge_config_dicts(dictA, dictB)
        assert dictA == {
            'key1': 'dictA.key1',
            'key2': [
                'dictA.key2-1',
                'dictA.key2-2',
                'dictB.key2-1',
                'dictB.key2-2',
            ],
            'key3': {
                'key3.1': 'dictA.key3.1',
                'key3.2': [
                    'dictA.key3.2-1',
                    'dictA.key3.2-2',
                    'dictB.key3.2-1',
                    'dictB.key3.2-2',
                ],
                'key3.3': 'dictB.key3.3',
                'key3.4': 'dictB.key3.4',
            },
            'key4': 'dictB.key4',
            'key5': 'dictB.key5',
        }

        many_recursions = {'foo': {'bar': {'foo': {'bar': 'foo'}}}}
        many_recursions_copy = deepcopy(many_recursions)

        with raises(DistMigrationConfigDataException):
            MigrationConfig._merge_config_dicts(many_recursions, many_recursions_copy)
