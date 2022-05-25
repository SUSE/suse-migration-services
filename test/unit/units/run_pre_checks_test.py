""" Tests for run_pre_checks"""
import logging

from unittest.mock import (
    patch
)

from pytest import (
    fixture
)
from suse_migration_services.units.run_pre_checks import (
    main
)
from suse_migration_services.defaults import Defaults


@patch.object(Defaults, 'get_migration_config_file')
@patch('suse_migration_services.logger.Logger.setup')
class TestRunPreChecks():
    """Tests to ensure pre_checks are called"""
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        """Setup capture log"""
        self._caplog = caplog

    @patch('suse_migration_services.prechecks.repos.remote_repos')
    @patch('suse_migration_services.prechecks.fs.encryption')
    @patch('suse_migration_services.prechecks.kernels.multiversion_and_multiple_kernels')
    def test_run_pre_checks(
        self,
        mock_pre_checks_kernel,
        mock_pre_checks_fs,
        mock_pre_checks_repos,
        mock_logger_setup,
        mock_get_migration_config_file
    ):

        mock_get_migration_config_file.return_value = \
            '../data/migration-config-initrd.yml'
        with self._caplog.at_level(logging.INFO):
            main()
            assert "Using the '--fix' option" in \
                self._caplog.text
