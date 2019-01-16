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
import os

# project
from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import log

from suse_migration_services.exceptions import (
    DistMigrationProductSetupException
)


def main():
    """
    DistMigration setup product

    Synchronize bind mounted /etc/products.d data into the migrated system
    """
    root_path = Defaults.get_system_root_path()

    try:
        # Note:
        # At the time this code was written fate#320882 was not
        # implemented which means only one registration server
        # (smt/rmt/scc) is used to answer the request for the
        # upgrade path from Distribution [A] to [B]. The approach
        # to overlay the systems' /etc/products.d directory with the
        # one from the migration live system will therefore not
        # hide product registrations from other registration
        # servers and is a functional fix to the distro_target
        # problem explained in units/prepare.py
        #
        # However once fate#320882 is resolved this will have an
        # impact on the zypper migration plugin code and depending
        # on that implementation it will no longer be allowed
        # to potentially hide product definitions as they are
        # defined on the system to migrate.
        products_metadata = os.sep.join(
            [root_path, 'etc', 'products.d']
        )
        log.info('Umounting {0}'.format(products_metadata))
        Command.run(
            ['umount', products_metadata]
        )
        log.info('Syncing product data to migrated system')
        Command.run(
            [
                'rsync', '-zav', '--delete', '/etc/products.d/',
                products_metadata + os.sep
            ]
        )
    except Exception as issue:
        message = 'Product setup failed with {0}'.format(issue)
        log.error(message)
        raise DistMigrationProductSetupException(message)
