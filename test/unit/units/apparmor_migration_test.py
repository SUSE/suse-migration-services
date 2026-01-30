from unittest.mock import patch
from pytest import raises
from tempfile import NamedTemporaryFile

from suse_migration_services.units.apparmor_migration import main
from suse_migration_services.exceptions import DistMigrationAppArmorMigrationException


@patch('suse_migration_services.logger.Logger.setup')
class TestAppArmorMigration(object):
    @patch('suse_migration_services.zypper.Zypper.install')
    @patch('suse_migration_services.defaults.Defaults.get_grub_default_file')
    def test_main(self, mock_get_grub_default_file, mock_Zypper_install, mock_logger_setup):
        test_data = NamedTemporaryFile()
        with open(test_data.name, 'w') as f:
            f.write('GRUB_CMDLINE_LINUX_DEFAULT="splash=silent security=apparmor"')
        mock_get_grub_default_file.return_value = test_data.name
        main()
        with open(test_data.name) as f:
            assert f.read() == 'GRUB_CMDLINE_LINUX_DEFAULT="splash=silent security=selinux"'
        mock_Zypper_install.assert_called_once_with(
            'patterns-base-selinux',
            extra_args=['--no-recommends'],
            raise_on_error=False,
            chroot='/system-root',
        )

    @patch('fileinput.input')
    def test_main_raises(self, mock_fileinput, mock_logger_setup):
        mock_fileinput.side_effect = Exception('error')
        with raises(DistMigrationAppArmorMigrationException):
            main()
