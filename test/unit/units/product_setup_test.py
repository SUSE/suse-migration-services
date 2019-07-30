from xml.etree.ElementTree import ElementTree
from unittest.mock import (
    patch, MagicMock
)
from pytest import raises

from suse_migration_services.units.product_setup import main
from suse_migration_services.exceptions import (
    DistMigrationProductSetupException
)


class TestProductSetup(object):
    @patch('suse_migration_services.defaults.Defaults.get_system_root_path')
    @patch('suse_migration_services.logger.log.error')
    @patch('suse_migration_services.logger.log.info')
    def test_main_raises_on_product_setup_flavors(
        self, mock_info, mock_error,
        mock_get_system_root_path
    ):
        mock_get_system_root_path.return_value = '../data/bad_products/too_many'
        with raises(DistMigrationProductSetupException):
            main()
        assert mock_error.called

    @patch('suse_migration_services.defaults.Defaults.get_system_root_path')
    @patch('suse_migration_services.logger.log.error')
    @patch('suse_migration_services.logger.log.info')
    def test_main_raises_on_product_setup_non_flavor(
        self, mock_info, mock_error,
        mock_get_system_root_path
    ):
        mock_get_system_root_path.return_value = '../data/bad_products/none'
        with raises(DistMigrationProductSetupException):
            main()
        mock_error.assert_called_with('Base Product update failed with: '
                                      'There is no baseproduct')

    @patch('suse_migration_services.suse_product.ElementTree')
    @patch('suse_migration_services.defaults.Defaults.get_system_root_path')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    @patch('os.path.exists')
    def test_main(
        self, mock_os_path_exists, mock_Command_run,
        mock_info, mock_get_system_root_path, mock_ElementTree
    ):
        xml = ElementTree()
        xml.write = MagicMock()
        mock_get_system_root_path.return_value = '../data'
        mock_ElementTree.return_value = xml
        mock_os_path_exists.return_value = True
        main()
        mock_Command_run.assert_called_once_with(
            [
                'rsync', '-zav', '--delete', '../data/etc/products.d/',
                '/tmp/products.d.backup/'
            ]
        )
        assert xml.findall('register/target') == []
        xml.write.assert_called_once_with(
            '../data/etc/products.d/SLES.prod',
            encoding='UTF-8', xml_declaration=True
        )
        assert mock_info.called
