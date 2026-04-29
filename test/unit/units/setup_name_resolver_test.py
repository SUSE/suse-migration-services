from unittest.mock import patch
from suse_migration_services.units.setup_name_resolver import main, SetupNameResolver


class TestSetupNameResolver:
    @patch('suse_migration_services.units.setup_name_resolver.ResolvConf.setup_live_system')
    @patch('suse_migration_services.logger.Logger.setup')
    def test_main(self, mock_logger_setup, mock_resolv_conf_setup_live_system):
        main()
        mock_resolv_conf_setup_live_system.assert_called_once()


    @patch('suse_migration_services.units.setup_name_resolver.ResolvConf.setup_live_system')
    @patch('suse_migration_services.logger.Logger.setup')
    def test_perform(self, mock_logger_setup, mock_resolv_conf_setup_live_system):
        resolver = SetupNameResolver()
        resolver.perform()

        mock_resolv_conf_setup_live_system.assert_called_once()
