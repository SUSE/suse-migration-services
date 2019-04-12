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
import os
import shutil

# project
from suse_migration_services.command import Command
from suse_migration_services.fstab import Fstab
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import log

from suse_migration_services.exceptions import (
    DistMigrationNameResolverException,
    DistMigrationHostNetworkException
)


def main():
    """
    DistMigration activate host network setup

    Setup and activate the network as it is setup on the host
    to become migrated. This includes the import of the resolver
    and network configuration from the migration host
    """
    root_path = Defaults.get_system_root_path()

    resolv_conf = os.sep.join(
        [root_path, 'etc', 'resolv.conf']
    )
    if not os.path.exists(resolv_conf):
        raise DistMigrationNameResolverException(
            'Could not find {0} on migration host'.format(resolv_conf)
        )

    shutil.copy(
        resolv_conf, '/etc/resolv.conf'
    )

    sysconfig_network = os.sep.join(
        [root_path, 'etc', 'sysconfig', 'network']
    )
    try:
        log.info('Running setup host network service')
        system_mount = Fstab()
        system_mount.read(
            Defaults.get_system_mount_info_file()
        )
        Command.run(
            ['mount', '--bind', sysconfig_network, '/etc/sysconfig/network']
        )
        system_mount.add_entry(
            sysconfig_network, '/etc/sysconfig/network'
        )
        system_mount.export(
            Defaults.get_system_mount_info_file()
        )
    except Exception as issue:
        log.error(
            'Preparation of migration host network failed with {0}'.format(
                issue
            )
        )
        raise DistMigrationHostNetworkException(
            'Preparation of migration host network failed with {0}'.format(
                issue
            )
        )
