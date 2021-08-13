import logging
import os
import yaml

from pytest import fixture
from unittest.mock import (
    patch, call
)

from suse_migration_services.units.post_mount_system import (
    main, log_env, update_env
)
from suse_migration_services.defaults import Defaults


class TestPostMountSystem(object):
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('os.path.exists')
    @patch.object(Defaults, 'get_migration_config_file')
    @patch('suse_migration_services.logger.Logger.setup')
    @patch('suse_migration_services.command.Command.run')
    @patch('suse_migration_services.defaults.Defaults.get_system_root_path')
    @patch('shutil.copy')
    def test_main(
        self, mock_shutil_copy, mock_get_system_root_path, mock_Command_run,
        mock_logger_setup, mock_get_migration_config_file, mock_os_path_exists
    ):
        mock_get_system_root_path.return_value = '../data'
        mock_get_migration_config_file.return_value = \
            '../data/migration-config.yml'
        mock_os_path_exists.side_effect = [True, False, True, False]
        main()
        assert mock_shutil_copy.call_args_list == [
            call('../data/etc/udev/rules.d/a.rules', '/etc/udev/rules.d'),
            call('../data/etc/udev/rules.d/b.rules', '/etc/udev/rules.d'),
            call('../data/etc/sysconfig/proxy', '/etc/sysconfig')
        ]
        assert mock_Command_run.call_args_list == [
            call(['mkdir', '-p', '/etc/udev/rules.d']),
            call(['mkdir', '-p', '/etc/sysconfig']),
            call(['udevadm', 'control', '--reload']),
            call(['udevadm', 'trigger', '--type=subsystems', '--action=add']),
            call(['udevadm', 'trigger', '--type=devices', '--action=add'])
        ]

    @patch.dict(os.environ, {'foo': 'bar', 'a': 'b'}, clear=True)
    def test_log_env(self):
        log = logging.getLogger('foo')
        with self._caplog.at_level(logging.INFO):
            log_env(log)
        assert ' Env variables' in self._caplog.text
        assert ' a: b\nfoo: bar\n\n' in self._caplog.text

    @patch.object(Defaults, 'get_proxy_path')
    @patch('suse_migration_services.units.post_mount_system.os')
    def test_update_env(self, mock_os, mock_proxy_path):
        with open('../data/migration-config-proxy.yml', 'r') as config:
            config_data = yaml.safe_load(config)
        mock_os.linesep = '\n'
        mock_proxy_path.return_value = '../data/etc/sysconfig/proxy'

        update_env(config_data.get('preserve'))
        mock_os.environ.update.assert_called_once()
