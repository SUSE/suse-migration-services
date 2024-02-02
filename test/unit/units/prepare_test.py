import os
import shutil
from tempfile import (
    NamedTemporaryFile,
    mkdtemp
)
from configparser import ConfigParser
from unittest.mock import (
    patch, call, Mock, MagicMock, mock_open
)

from pytest import raises

from suse_migration_services.units.prepare import (
    main, update_regionsrv_setup, get_regionsrv_client_file_location,
    get_regionsrv_certs_path, report_if_regionsrv_certs_not_found
)

from suse_migration_services.suse_connect import SUSEConnect
from suse_migration_services.fstab import Fstab
from suse_migration_services.exceptions import (
    DistMigrationZypperMetaDataException
)


@patch('suse_migration_services.units.prepare.update_regionsrv_setup')
@patch('suse_migration_services.logger.Logger.setup')
@patch('suse_migration_services.units.prepare.Fstab')
@patch('suse_migration_services.command.Command.run')
class TestSetupPrepare(object):
    @patch('suse_migration_services.units.prepare.get_regionsrv_client_file_location')
    @patch('shutil.copy')
    @patch('os.listdir')
    @patch('builtins.open')
    @patch('os.path.exists')
    def test_main_raises_on_zypp_bind(
        self, mock_os_path_exists, mock_open, mock_os_listdir,
        mock_shutil_copy, mock_get_regionsrv_client_file_location,
        mock_Command_run, mock_Fstab, mock_logger_setup,
        mock_update_regionsrv_setup
    ):
        mock_os_listdir.return_value = None
        mock_os_path_exists.return_value = True
        mock_Command_run.side_effect = [
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            Exception
        ]
        with raises(DistMigrationZypperMetaDataException):
            main()

    @patch('suse_migration_services.units.prepare.get_regionsrv_certs_path')
    @patch('suse_migration_services.units.prepare.get_regionsrv_client_file_location')
    @patch('shutil.copy')
    @patch('os.listdir')
    @patch('os.path.exists')
    def test_main_raises_on_get_regionsrv_client_file_location(
        self, mock_os_path_exists, mock_os_listdir, mock_shutil_copy,
        mock_get_regionsrv_client_file_location,
        mock_get_regionsrv_certs_path,
        mock_Command_run,
        mock_Fstab, mock_logger_setup,
        mock_update_regionsrv_setup
    ):
        mock_os_listdir.return_value = None
        # need to override the get_regionsrv_certs_path() call to avoid
        # introducing a additional open()
        mock_get_regionsrv_certs_path.return_value = \
            '/var/lib/regionService/certs'
        mock_get_regionsrv_client_file_location.side_effect = \
            [DistMigrationZypperMetaDataException('foo')]
        mock_os_path_exists.return_value = True
        mock_Command_run.side_effect = [
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            Exception
        ]
        with patch('builtins.open', mock_open(read_data='foo.susecloud.net')):
            with raises(DistMigrationZypperMetaDataException):
                main()

    @patch('suse_migration_services.units.prepare.get_regionsrv_client_file_location')
    @patch('shutil.copy')
    @patch('os.listdir')
    def test_main_raises_on_regionsrv_client_file_exists(
        self, mock_os_listdir, mock_shutil_copy,
        mock_get_regionsrv_client_file_location, mock_Command_run,
        mock_Fstab, mock_logger_setup,
        mock_update_regionsrv_setup
    ):
        mock_os_listdir.return_value = None
        mock_get_regionsrv_client_file_location.return_value = \
            ['/foo']
        mock_Command_run.side_effect = [
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            Exception
        ]
        with patch('builtins.open', mock_open(read_data='foo.susecloud.net')):
            with raises(DistMigrationZypperMetaDataException):
                main()

    @patch('suse_migration_services.units.prepare.get_regionsrv_client_file_location')
    @patch('shutil.copy')
    @patch('os.listdir')
    @patch('builtins.open')
    @patch('os.path.exists')
    def test_main_raises_and_umount_file_system(
        self, mock_os_path_exists, mock_open_hosts_file, mock_os_listdir,
        mock_shutil_copy, mock_get_regionsrv_client_file_location,
        mock_Command_run, mock_Fstab,
        mock_logger_setup, mock_update_regionsrv_setup
    ):
        fstab = Fstab()
        fstab_mock = Mock()
        fstab_mock.read.return_value = fstab.read('../data/bind-mounted.fstab')
        fstab_mock.get_devices.return_value = fstab.get_devices()
        fstab_mock.export.side_effect = Exception
        mock_Fstab.return_value = fstab_mock
        mock_os_path_exists.return_value = True
        with raises(DistMigrationZypperMetaDataException):
            main()
            assert mock_Command_run.call_args_list == [
                call(['ip', 'a'], raise_on_error=False),
                call(['ip', 'r'], raise_on_error=False),
                call(['cat', '/etc/resolv.conf'], raise_on_error=False),
                call(['cat', '/proc/net/bonding/bond*'], raise_on_error=False),
                call(['umount', '/system-root/sys'], raise_on_error=False),
                call(['umount', '/system-root/proc'], raise_on_error=False),
                call(['umount', '/system-root/dev'], raise_on_error=False)
            ]

    @patch('suse_migration_services.units.prepare.get_regionsrv_certs_path')
    @patch('os.path.isfile')
    @patch.object(SUSEConnect, 'is_registered')
    @patch('suse_migration_services.units.prepare.MigrationConfig')
    @patch('suse_migration_services.units.prepare.Path')
    @patch('shutil.copy')
    @patch('os.listdir')
    @patch('os.path.isdir')
    @patch('os.path.islink')
    @patch('os.readlink')
    @patch('os.path.exists')
    def test_main(
        self, mock_os_path_exists, mock_readlink, mock_os_path_islink,
        mock_path_isdir, mock_os_listdir,
        mock_shutil_copy, mock_Path, mock_MigrationConfig,
        mock_is_registered, mock_is_file,
        mock_get_regionsrv_certs_path,
        mock_Command_run,
        mock_Fstab, mock_logger_setup,
        mock_update_regionsrv_setup
    ):

        mock_readlink.return_value = 'link_target'
        mock_path_isdir.side_effect = [True, True, True, True]
        migration_config = Mock()
        migration_config.is_zypper_migration_plugin_requested.return_value = \
            True
        mock_MigrationConfig.return_value = migration_config
        fstab = Mock()
        mock_Fstab.return_value = fstab
        mock_os_listdir.side_effect = [
            ['foo', 'bar'],
            ['foo', 'bar'],
            ['fooSMT'],
            ['fooSMT']
        ]
        mock_os_path_islink.side_effect = [
            False, False, False, True
        ]
        mock_os_path_exists.side_effect = [
            True, True, True, True, False, True, True, True
        ]
        mock_is_registered.return_value = True
        mock_Command_run.side_effect = [
            MagicMock(),
            MagicMock(),
            Exception('no zypper log'),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock()
        ]
        mock_shutil_copy.side_effect = [
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            FileNotFoundError('cert copy failed')
        ]
        mock_is_file.return_value = True
        # need to override the get_regionsrv_certs_path() call to avoid
        # introducing a additional open() call
        mock_get_regionsrv_certs_path.return_value = \
            '/var/lib/regionService/certs'
        with patch('builtins.open', mock_open(read_data='foo.susecloud.net')):
            main()
        assert mock_shutil_copy.call_args_list == [
            call('/system-root/etc/SUSEConnect', '/etc/SUSEConnect'),
            call(
                '/system-root/etc/regionserverclnt.cfg',
                '/etc/regionserverclnt.cfg'
            ),
            call('/system-root/etc/hosts', '/etc/hosts'),
            call(
                '/system-root/usr/share/pki/trust/anchors/foo',
                '/usr/share/pki/trust/anchors/'
            ),
            call(
                '/system-root/usr/share/pki/trust/anchors/bar',
                '/usr/share/pki/trust/anchors/'
            ),
            call(
                '/system-root/etc/pki/trust/anchors/foo',
                '/etc/pki/trust/anchors/'
            ),
            call(
                '/system-root/link_target',
                '/etc/pki/trust/anchors/'
            )
        ]
        mock_Path.call_args_list == [
            call(['/var/cache/cloudregister']),
            call(['/usr/share/pki/trust/anchors']),
            call(['/etc/pki/trust/anchors'])
        ]
        assert mock_Command_run.call_args_list == [
            call(
                ['update-ca-certificates']
            ),
            call(
                ['update-ca-certificates']
            ),
            call(
                [
                    'mount', '--bind', '/system-root/var/log/zypper.log',
                    '/var/log/zypper.log'
                ]
            ),
            call(
                ['ip', 'a'], raise_on_error=False
            ),
            call(
                ['ip', 'r'], raise_on_error=False
            ),
            call(
                ['cat', '/etc/resolv.conf'], raise_on_error=False
            ),
            call(
                ['cat', '/proc/net/bonding/bond*'], raise_on_error=False
            ),
            call(
                ['mount', '--bind', '/system-root/etc/zypp', '/etc/zypp']
            ),
            call(
                [
                    'mount', '--bind',
                    '/system-root/usr/lib/zypp/plugins/services',
                    '/usr/lib/zypp/plugins/services'
                ]
            ),
            call(
                [
                    'mount', '--bind', '/system-root/var/cache/cloudregister',
                    '/var/cache/cloudregister'
                ]
            ),
            call(
                [
                    'mount', '--bind', '/system-root/var/lib/regionService/certs',
                    '/var/lib/regionService/certs'
                ]
            ),
            call(
                ['/usr/sbin/updatesmtcache']
            )
        ]
        fstab.read.assert_called_once_with(
            '/etc/system-root.fstab'
        )
        assert fstab.add_entry.call_args_list == [
            call(
                '/system-root/etc/zypp', '/etc/zypp'
            ),
            call(
                '/system-root/usr/lib/zypp/plugins/services',
                '/usr/lib/zypp/plugins/services'
            )
        ]
        fstab.export.assert_called_once_with(
            '/etc/system-root.fstab'
        )
        mock_Command_run.assert_any_call(
            ['cat', '/proc/net/bonding/bond*'], raise_on_error=False
        )

    @patch('suse_migration_services.units.prepare.get_regionsrv_certs_path')
    @patch('suse_migration_services.units.prepare.get_regionsrv_client_file_location')
    @patch.object(SUSEConnect, 'is_registered')
    @patch('suse_migration_services.units.prepare.MigrationConfig')
    @patch('suse_migration_services.units.prepare.Path')
    @patch('shutil.copy')
    @patch('os.listdir')
    @patch('os.path.exists')
    def test_main_no_registered_instance(
        self, mock_os_path_exists, mock_os_listdir, mock_shutil_copy,
        mock_Path, mock_MigrationConfig, mock_is_registered,
        mock_get_regionsrv_client_file_location,
        mock_get_regionsrv_certs_path, mock_Command_run,
        mock_Fstab, mock_logger_setup, mock_update_regionsrv_setup
    ):
        migration_config = Mock()
        migration_config.is_zypper_migration_plugin_requested.return_value = \
            True
        mock_MigrationConfig.return_value = migration_config
        fstab = Mock()
        mock_Fstab.return_value = fstab
        # need to override the get_regionsrv_certs_path() call to avoid
        # introducing a additional open() call
        mock_get_regionsrv_certs_path.return_value = \
            '/var/lib/regionService/certs'
        mock_os_listdir.return_value = ['foo', 'bar']
        mock_os_path_exists.return_value = True
        mock_is_registered.return_value = False
        with patch('builtins.open', mock_open(read_data='foo.susecloud.net')):
            with raises(DistMigrationZypperMetaDataException):
                main()

    @patch('suse_migration_services.units.prepare.get_regionsrv_client_file_location')
    @patch('os.path.exists')
    def test_update_regionsrv_setup(
        self, mock_os_path_exists, mock_get_regionsrv_client_file_location,
        mock_Command_run, mock_Fstab, mock_logger_setup,
        mock_update_regionsrv_setup
    ):
        mock_command_return_values = [
            Mock(output='/dev/sda3 part\n/dev/sda disk'),
            Mock(output='dev/sda3\n')
        ]

        def command_returns(arg):
            return mock_command_return_values.pop()

        mock_Command_run.side_effect = command_returns

        tmp_regionserverclnt = NamedTemporaryFile()
        shutil.copy(
            '../data/regionserverclnt-azure.cfg', tmp_regionserverclnt.name
        )
        update_regionsrv_setup(
            '/system-root', tmp_regionserverclnt.name
        )
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'findmnt', '--first', '--noheadings',
                    '--output', 'SOURCE', '--mountpoint', '/system-root'
                ]
            ),
            call(
                [
                    'lsblk', '-p', '-n', '-r', '-s',
                    '-o', 'NAME,TYPE', 'dev/sda3'
                ]
            )
        ]
        regionsrv_setup = ConfigParser()
        regionsrv_setup.read(tmp_regionserverclnt.name)
        assert regionsrv_setup.get('instance', 'dataProvider') == \
            '/usr/bin/azuremetadata --api latest --subscriptionId --billingTag ' \
            '--attestedData --signature --xml --device /dev/sda'

    @patch('os.listdir')
    @patch('os.path.isdir')
    @patch('os.path.exists')
    def test_old_regionsrv_client_file_location(
        self, mock_os_path_exists, mock_path_isdir, mock_os_listdir,
        mock_Command_run, mock_Fstab, mock_logger_setup,
        mock_update_regionsrv_setup,
    ):
        mock_path_isdir.side_effect = [False, True]
        mock_os_listdir.return_value = ['fooSMT']
        assert get_regionsrv_client_file_location('/foo') == \
            '/foo/var/lib/cloudregister'

    @patch('os.path.isdir')
    @patch('os.path.exists')
    def test_get_regionsrv_client_file_location_raises(
        self, mock_os_path_exists, mock_path_isdir,
        mock_Command_run, mock_Fstab, mock_logger_setup,
        mock_update_regionsrv_setup,
    ):
        mock_path_isdir.side_effect = [False, False]
        with raises(DistMigrationZypperMetaDataException):
            get_regionsrv_client_file_location('/foo')

    def test_get_regionsrv_certs_path_certlocation(
        self,
        mock_Command_run,
        mock_Fstab,
        mock_logger_setup,
        mock_update_regionsrv_setup,
    ):
        tmp_regionserverclnt = NamedTemporaryFile()

        # assert fallback path returned if client config is missing
        assert get_regionsrv_certs_path(
            '/some/file/that/does/not/exist',
            'foo'
        ) == 'foo'

        # assert fallback path returned if client config is empty
        assert get_regionsrv_certs_path(
            tmp_regionserverclnt.name,
            'foo'
        ) == 'foo'

        # test we get the fallback certlocation when none specified in config
        shutil.copy(
            '../data/regionserverclnt-nocertlocation.cfg',
            tmp_regionserverclnt.name
        )

        assert get_regionsrv_certs_path(
            tmp_regionserverclnt.name,
            'foo'
        ) == 'foo'

        # test we get the standard certlocation from the config
        shutil.copy(
            '../data/regionserverclnt-certlocation.cfg',
            tmp_regionserverclnt.name
        )

        assert get_regionsrv_certs_path(
            tmp_regionserverclnt.name,
            'foo'
        ) == '/usr/lib/regionService/certs'

        # test we get the old certlocation from an old config
        shutil.copy(
            '../data/regionserverclnt-oldcertlocation.cfg',
            tmp_regionserverclnt.name
        )

        assert get_regionsrv_certs_path(
            tmp_regionserverclnt.name,
            'foo'
        ) == '/var/lib/regionService/certs'

    def test_report_if_regionsrv_certs_not_found(
        self,
        mock_Command_run,
        mock_Fstab,
        mock_logger_setup,
        mock_update_regionsrv_setup
    ):
        tmp_certs_dir = mkdtemp()

        log = Mock(spec=['info'])

        # verify that log.info() is called when dir has no pem files
        report_if_regionsrv_certs_not_found(tmp_certs_dir, log)
        assert len(log.info.call_args_list) == 1

        # reset the log mock object
        log.reset_mock()

        # verify that log.info() is not called when dir has pem files
        tmp_pem_path = os.path.join(tmp_certs_dir, 'dummy_cert.pem')
        open(tmp_pem_path, 'w').close()
        report_if_regionsrv_certs_not_found(tmp_certs_dir, log)
        assert len(log.info.call_args_list) == 0

        # cleanup tmp_certs_dir
        shutil.rmtree(tmp_certs_dir, ignore_errors=True)
