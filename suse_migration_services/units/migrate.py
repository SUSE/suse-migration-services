# Copyright (c) 2018 SUSE Linux LLC.  All rights reserved.
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
import yaml
import os
import shutil

# project
from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import log

from suse_migration_services.exceptions import (
    DistMigrationZypperException
)


def main():
    """
    DistMigration run zypper based migration

    Call zypper migration plugin and migrate the system.
    The output of the call is logged on the system to migrate
    """
    root_path = Defaults.get_system_root_path()

    try:
        log.info('Running migrate service')
        bash_command = ' '.join(
            [
                'zypper', 'migration',
                '--non-interactive',
                '--gpg-auto-import-keys',
                '--no-selfupdate',
                '--auto-agree-with-licenses',
                '--product', get_migration_product(),
                '--root', root_path,
                '&>>', Defaults.get_migration_log_file()
            ]
        )
        Command.run(
            ['bash', '-c', bash_command]
        )
    except Exception as issue:
        etc_issue_path = os.sep.join(
            [root_path, 'etc/issue']
        )
        log_path_migrated_system = os.sep + os.path.relpath(
            Defaults.get_migration_log_file(), root_path
        )
        with open(etc_issue_path, 'w') as issue_file:
            issue_file.write(
                'Migration has failed, for further details see {0}'
                .format(log_path_migrated_system)
            )
        debug_file = Defaults.get_system_migration_debug_file()
        migration_debug_path = os.sep.join(
            [root_path, debug_file]
        )
        if os.path.exists(migration_debug_path):
            shutil.copy(
                migration_debug_path,
                os.sep + debug_file
            )

        log.error('migrate service failed with {0}'.format(issue))
        raise DistMigrationZypperException(
            'Migration failed with {0}'.format(
                issue
            )
        )


def get_migration_product():
    """
    Returns the full qualified product

    The value returned is passed to the --product option in the
    zypper migration call
    """
    config = _read_migration_config()
    return config['migration']['target']['product']


def _read_migration_config():
    with open(Defaults.get_migration_config_file(), 'r') as config:
        return yaml.load(config)
