from unittest.mock import (
    patch, Mock
)

from suse_migration_services.migration_target import MigrationTarget


class TestMigrationTarget(object):
    @patch('platform.machine')
    @patch('os.path.isfile')
    @patch('suse_migration_services.migration_target.glob')
    @patch('suse_migration_services.migration_target.MigrationConfig')
    def test_get_migration_target_empty(
        self, mock_MigrationConfig, mock_glob, mock_os_path_isfile,
        mock_platform_machine
    ):
        migration_config = Mock()
        migration_config.config_data = {}
        mock_MigrationConfig.return_value = migration_config
        mock_platform_machine.return_value = 'x86_64'
        mock_glob.return_value = []
        mock_os_path_isfile.return_value = False
        assert MigrationTarget.get_migration_target() == {}

    @patch('suse_migration_services.migration_target.MigrationConfig')
    def test_get_migration_target_configured(self, mock_MigrationConfig):
        migration_config = Mock()
        migration_config.config_data = {
            'migration_product': 'SLES/15.4/x86_64'
        }
        mock_MigrationConfig.return_value = migration_config
        assert MigrationTarget.get_migration_target() == {
            'identifier': 'SLES',
            'version': '15.4',
            'arch': 'x86_64'
        }

    @patch('platform.machine')
    @patch('os.path.isfile')
    @patch('suse_migration_services.migration_target.glob')
    @patch('suse_migration_services.migration_target.MigrationConfig')
    def test_get_migration_target_sles15(
        self, mock_MigrationConfig, mock_glob, mock_os_path_isfile,
        mock_platform_machine
    ):
        migration_config = Mock()
        migration_config.config_data = {}
        mock_MigrationConfig.return_value = migration_config
        mock_platform_machine.return_value = 'x86_64'
        mock_glob.return_value = [
            '/migration-image/SLES15-Migration.x86_64-2.1.9-Build6.64.99.iso'
        ]
        mock_os_path_isfile.return_value = False
        assert MigrationTarget.get_migration_target() == {
            'identifier': 'SLES',
            'version': '15.4',
            'arch': 'x86_64'
        }

    @patch('platform.machine')
    @patch('os.path.isfile')
    @patch('suse_migration_services.migration_target.glob')
    @patch('suse_migration_services.migration_target.MigrationConfig')
    def test_get_migration_target_sles16(
        self, mock_MigrationConfig, mock_glob, mock_os_path_isfile,
        mock_platform_machine
    ):
        migration_config = Mock()
        migration_config.config_data = {}
        mock_MigrationConfig.return_value = migration_config
        mock_glob.return_value = [
            '/migration-image/SLES16-Migration.x86_64-2.1.23-Build2.1.iso'
        ]
        mock_platform_machine.return_value = 'x86_64'
        mock_os_path_isfile.return_value = False  # No /etc/sle-migration-service.yml
        assert MigrationTarget.get_migration_target() == {
            'identifier': 'SLES',
            'version': '16.0',
            'arch': 'x86_64'
        }
