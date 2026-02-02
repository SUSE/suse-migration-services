from xml.etree.ElementTree import ElementTree
from unittest.mock import patch, Mock

from pytest import raises

from suse_migration_services.suse_product import SUSEBaseProduct
from suse_migration_services.defaults import Defaults
from suse_migration_services.exceptions import DistMigrationSUSEBaseProductException


@patch('suse_migration_services.suse_product.ElementTree')
class TestSUSEProduct(object):
    @patch.object(Defaults, 'get_system_root_path')
    def setup_method(self, method, mock_get_system_root_path):
        mock_get_system_root_path.return_value = '../data/'
        self.suse_product = SUSEBaseProduct(Mock())

    @patch.object(Defaults, 'get_system_root_path')
    def test_baseproduct_raises(self, mock_get_system_root_path, mock_ElementTree_parse):
        mock_ElementTree_parse.return_value.parse.side_effect = Exception
        mock_get_system_root_path.return_value = '../data'
        with raises(DistMigrationSUSEBaseProductException):
            SUSEBaseProduct(Mock())

    @patch.object(SUSEBaseProduct, 'backup_products_metadata')
    def test_delete_target_registration_raises(self, mock_backup_product_md, mock_ElementTree):
        mock_ElementTree().parse.side_effect = Exception
        self.suse_product.delete_target_registration()

    def test_baseproduct_tag_text(self, mock_ElementTree):
        xml = ElementTree()
        mock_ElementTree.return_value = xml
        product_name = self.suse_product.get_tag('name')
        assert product_name[0] == 'SLES'

    def test_baseproduct_tag_text_raises(self, mock_ElementTree):
        mock_ElementTree().parse.side_effect = Exception
        self.suse_product.get_tag('name')
