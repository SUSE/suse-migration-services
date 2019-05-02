from unittest.mock import patch

from suse_migration_services.migration_config import MigrationConfig
from suse_migration_services.defaults import Defaults


class TestMigrationConfig(object):
    @patch.object(Defaults, 'get_migration_config_file')
    def setup(self, mock_get_migration_config_file):
        mock_get_migration_config_file.return_value = \
            '../data/migration-config.yml'
        self.config = MigrationConfig()

    def test_get_migration_product(self):
        assert self.config.get_migration_product() == 'foo'
