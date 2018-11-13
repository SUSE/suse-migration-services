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

# project
from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults

from suse_migration_services.exceptions import (
    DistMigrationZypperException
)


def main():
    """
    DistMigration run zypper based migration

    Call zypper migration plugin and migrate the system
    """
    root_path = Defaults.get_system_root_path()

    try:
        Command.run(
            [
                'zypper', 'migration',
                '--non-interactive',
                '--gpg-auto-import-keys',
                '--no-selfupdate',
                '--auto-agree-with-licenses',
                '--product', get_migration_product(),
                '--root', root_path
            ]
        )
    except Exception as issue:
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
