# Copyright (c) 2019 SUSE Linux LLC.  All rights reserved.
#
# This file is part of suse-migration-services.
#
# suse-migration-services is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# suse-migration-services is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with suse-migration-services. If not, see <http://www.gnu.org/licenses/>
#
import logging
import os
import shutil
import glob

# project
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger
from suse_migration_services.migration_config import MigrationConfig
from suse_migration_services.command import Command


def main():
    """
    DistMigration post mount actions

    Preserve custom data file(s) e.g udev rules from the system
    to be migrated to the live migration system and activate
    those file changes to become effective
    """
    Logger.setup()
    log = logging.getLogger(Defaults.get_migration_log_name())
    root_path = Defaults.get_system_root_path()
    log.info('Running post mount actions')

    migration_config = MigrationConfig()
    preserve_info = migration_config.get_preserve_info()
    if preserve_info:
        for _, preserve_files in preserve_info.items():
            for preserve_file in preserve_files:
                source_glob = os.path.normpath(
                    os.sep.join([root_path, preserve_file])
                )
                for source_file in glob.glob(source_glob):
                    target_dir = os.path.dirname(source_file)[len(root_path):]
                    log.info(
                        'Copy file: {0} to: {1}'.format(
                            source_file, target_dir
                        )
                    )
                    if not os.path.exists(target_dir):
                        Command.run(
                            ['mkdir', '-p', target_dir]
                        )
                    shutil.copy(source_file, target_dir)
        if 'rules' in preserve_info.keys():
            Command.run(
                ['udevadm', 'control', '--reload']
            )
            Command.run(
                ['udevadm', 'trigger', '--type=subsystems', '--action=add']
            )
            Command.run(
                ['udevadm', 'trigger', '--type=devices', '--action=add']
            )


def update_env(preserve_info):
    proxy_env = {}
    for _, preserve_files in preserve_info.items():
        if Defaults.get_proxy_path() in preserve_files:
            with open(Defaults.get_proxy_path(), 'r') as proxy_file:
                for line in proxy_file.readlines():
                    if not (line.startswith('#') or line.startswith(os.linesep)):
                        # DMS currently takes http, https and ftp protocols
                        # into consideration, so lower case them is ok
                        key_value = line.lower(). \
                            replace(os.linesep, ''). \
                            replace('"', ''). \
                            split('=')
                        proxy_env.update(dict([key_value]))
    if proxy_env.get('proxy_enabled') == 'yes':
        del proxy_env['proxy_enabled']
        os.environ.update(proxy_env)


def log_env(log):
    """Provide information about the current environment."""
    log.info('Env variables')
    env = ''
    for key, value in sorted(os.environ.items()):
        env += '{key}: {value}{newline}'.format(
            key=key, value=value, newline=os.linesep
        )
    log.info(env)
