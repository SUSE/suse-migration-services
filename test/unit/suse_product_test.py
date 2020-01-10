from xml.etree.ElementTree import ElementTree
from unittest.mock import patch

from pytest import raises

from suse_migration_services.suse_product import SUSEBaseProduct
from suse_migration_services.defaults import Defaults
from suse_migration_services.exceptions import (
    DistMigrationSUSEBaseProductException
)


class TestSUSEProduct(object):
    @patch.object(Defaults, 'get_system_root_path')
    def setup(
        self, mock_get_system_root_path
    ):
        mock_get_system_root_path.return_value = '../data/'
        self.suse_product = SUSEBaseProduct()

    @patch.object(Defaults, 'get_system_root_path')
    @patch('suse_migration_services.suse_product.ElementTree.parse')
    def test_baseproduct_raises(
        self, mock_ElementTree_parse, mock_get_system_root_path
    ):
        mock_ElementTree_parse.side_effect = Exception
        mock_get_system_root_path.return_value = '../data'
        with raises(DistMigrationSUSEBaseProductException):
            SUSEBaseProduct()

    @patch.object(SUSEBaseProduct, 'backup_products_metadata')
    @patch('suse_migration_services.suse_product.ElementTree')
    def test_delete_target_registration_raises(
        self, mock_ElementTree, mock_backup_product_md
    ):
        mock_ElementTree().parse.side_effect = Exception
        self.suse_product.delete_target_registration()

    @patch('suse_migration_services.suse_product.ElementTree')
    def test_baseproduct_tag_text(
        self, mock_ElementTree
    ):
        xml = ElementTree()
        mock_ElementTree.return_value = xml
        product_name = self.suse_product.get_tag('name')
        assert product_name[0] == 'SLES'

    @patch('suse_migration_services.suse_product.ElementTree')
    def test_baseproduct_tag_text_raises(self, mock_ElementTree):
        mock_ElementTree().parse.side_effect = Exception
        self.suse_product.get_tag('name')
