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

    @patch.object(Defaults, 'get_os_release')
    @patch.object(Defaults, 'get_migration_image_root_path')
    def test_get_product_name(
        self, mock_get_migration_image_root_path, mock_get_os_release, mock_ElementTree
    ):
        # the system to migrate is SLES/12.3/x86_64, see ../data/etc/products.d,
        # the migration image provides SLES_SAP/16.1/aarch64
        mock_ElementTree.return_value = ElementTree()
        mock_get_migration_image_root_path.return_value = '../data/migration-image'
        mock_get_os_release.return_value = Mock(version_id='16.1')
        assert self.suse_product.get_product_name() == 'SLES_SAP/16.1/x86_64'

    @patch.object(Defaults, 'get_migration_image_root_path')
    def test_get_product_name_without_migration_image_product(
        self, mock_get_migration_image_root_path, mock_ElementTree
    ):
        mock_ElementTree.return_value = ElementTree()
        mock_get_migration_image_root_path.return_value = '../data/no-such-image'
        assert self.suse_product.get_product_name() is None
