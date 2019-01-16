from unittest.mock import (
    patch, call
)
from pytest import raises

from suse_migration_services.units.product_setup import main
from suse_migration_services.exceptions import (
    DistMigrationProductSetupException
)


class TestProductSetup(object):
    @patch('suse_migration_services.logger.log.error')
    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    def test_main_raises_on_product_setup(
        self, mock_Command_run, mock_info, mock_error
    ):
        mock_Command_run.side_effect = Exception
        with raises(DistMigrationProductSetupException):
            main()
            assert mock_info.called
            assert mock_error.called

    @patch('suse_migration_services.logger.log.info')
    @patch('suse_migration_services.command.Command.run')
    def test_main(
        self, mock_Command_run, mock_info
    ):
        main()
        assert mock_Command_run.call_args_list == [
            call(
                ['umount', '/system-root/etc/products.d']
            ),
            call(
                [
                    'rsync', '-zav', '--delete',
                    '/etc/products.d/',
                    '/system-root/etc/products.d/'
                ]
            )
        ]
        assert mock_info.called
