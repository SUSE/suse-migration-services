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
import logging
import os
import shutil

# project
from suse_migration_services.command import Command
from suse_migration_services.fstab import Fstab
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger

from suse_migration_services.exceptions import (
    DistMigrationNameResolverException,
)


def main():
    """
    DistMigration setup name resolver

    Setup /etc/resolv.conf by importing the resolver configuration
    from the migration host
    """
    Logger.setup()
    log = logging.getLogger(Defaults.get_migration_log_name())
    root_path = Defaults.get_system_root_path()

    system_mount = Fstab()
    system_mount.read(
        Defaults.get_system_mount_info_file()
    )

    resolv_conf = os.sep.join(
        [root_path, 'etc', 'resolv.conf']
    )
    try:
        log.info('Running setup resolver service')
        if has_host_resolv_setup(resolv_conf):
            log.info('Copying {}'.format(resolv_conf))
            shutil.copy(
                resolv_conf, '/etc/resolv.conf'
            )
        else:
            log.info('Empty {0}, bind mounting /etc/resolv.conf to {0}'.format(resolv_conf))
            Command.run(
                [
                    'mount', '--bind', '/etc/resolv.conf',
                    resolv_conf
                ]
            )
            system_mount.add_entry(
                '/etc/resolv.conf', resolv_conf
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
        raise DistMigrationNameResolverException(
            'Preparation of migration host network failed with {0}'.format(
                issue
            )
        ) from issue


def has_host_resolv_setup(resolv_conf_path):
    with open(resolv_conf_path, 'r') as resolv:
        for line in resolv:
            # check there is useful information in the remaining lines
            if line.startswith('search') or line.startswith('nameserver'):
                return True
    return False
