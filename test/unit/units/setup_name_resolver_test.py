from unittest.mock import patch, MagicMock
from suse_migration_services.units.setup_name_resolver import main, SetupNameResolver


class TestSetupNameResolver:
    @patch('suse_migration_services.units.setup_name_resolver.ResolvConf')
    @patch('suse_migration_services.logger.Logger.setup')
    def test_main(self, mock_logger_setup, mock_resolv_conf_cls):
        mock_resolv_conf_instance = MagicMock()
        mock_resolv_conf_cls.return_value = mock_resolv_conf_instance

        main()

        mock_resolv_conf_cls.assert_called_once()
        mock_resolv_conf_instance.prepare_resolv_conf.assert_called_once()

    @patch('suse_migration_services.units.setup_name_resolver.ResolvConf')
    @patch('suse_migration_services.logger.Logger.setup')
    def test_perform(self, mock_logger_setup, mock_resolv_conf_cls):
        mock_resolv_conf_instance = MagicMock()
        mock_resolv_conf_cls.return_value = mock_resolv_conf_instance

        resolver = SetupNameResolver()
        resolver.perform()

        mock_resolv_conf_instance.prepare_resolv_conf.assert_called_once()
