from unittest.mock import patch
from pytest import raises

from suse_migration_services.migration_config import MigrationConfig
from suse_migration_services.defaults import Defaults
from suse_migration_services.exceptions import (
    DistMigrationProductNotFoundException
)


class TestMigrationConfig(object):
    @patch.object(Defaults, 'get_migration_config_file')
    def setup(self, mock_get_migration_config_file):
        mock_get_migration_config_file.return_value = \
            '../data/migration-config.yml'
        self.config = MigrationConfig()

    def test_get_migration_product(self):
        assert self.config.get_migration_product() == 'SLES/15/x86_64'

    @patch('suse_migration_services.logger.log.error')
    def test_get_migration_product_targets(self, mock_error):
        self.config.config_data = {'not_migration_product': 'another_info'}

        with raises(DistMigrationProductNotFoundException):
            self.config.get_migration_product()
            assert mock_error.called

    def test_is_debug_requested(self):
        assert not self.config.is_debug_requested()
