import io
from unittest.mock import (
    patch, MagicMock
)

from suse_migration_services.logger import Logger


class TestLogger:
    @patch('suse_migration_services.logger.Path.create')
    def test_setup(self, mock_Path_create):
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            logger = Logger()
            logger.setup()
            mock_Path_create.assert_called_once_with(
                '/system-root/var/log'
            )
            mock_open.assert_called_once_with(
                '/system-root/var/log/distro_migration.log', 'a', encoding=None
            )

    @patch('suse_migration_services.logger.Path.create')
    def test_setup_no_system_root(self, mock_Path_create):
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            logger = Logger()
            logger.setup(system_root=False)
            mock_Path_create.assert_called_once_with(
                '/var/log'
            )
            mock_open.assert_called_once_with(
                '/var/log/distro_migration.log', 'a', encoding=None
            )
