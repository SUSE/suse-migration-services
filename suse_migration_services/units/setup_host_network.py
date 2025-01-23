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
import glob
import os
import shutil

# project
from suse_migration_services.command import Command
from suse_migration_services.fstab import Fstab
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger

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
    sysconfig_network_providers = os.sep.join(
        [root_path, 'etc', 'sysconfig', 'network', 'providers']
    )
    sysconfig_network_setup = os.sep.join(
        [root_path, 'etc', 'sysconfig', 'network', '*']
    )
    try:
        log.info('Running setup host network service')
        if os.path.exists(sysconfig_network_providers):
            Command.run(
                [
                    'mount', '--bind', sysconfig_network_providers,
                    '/etc/sysconfig/network/providers'
                ]
            )
            system_mount.add_entry(
                sysconfig_network_providers, '/etc/sysconfig/network/providers'
            )
        for network_setup in glob.glob(sysconfig_network_setup):
            if os.path.isfile(network_setup):
                shutil.copy(
                    network_setup, '/etc/sysconfig/network'
                )
        Command.run(
            ['systemctl', 'reload', 'network']
        )
        if has_host_resolv_setup(resolv_conf):
            log.info('Copying {}'.format(resolv_conf))
            shutil.copy(
                resolv_conf, '/etc/resolv.conf'
            )
        else:
            # ensure resolv.conf won't be a symlink on migrated system, create an empty file instead to allow bind mount
            if os.path.islink(resolv_conf):
                log.info('{0} is a symlink, renaming it to {0}.pre-migration, bind mounting /etc/resolv.conf to {0}'.format(resolv_conf))
                os.replace(resolv_conf,resolv_conf+'.pre-migration')
                open(resolv_conf,'w').close()
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
        raise DistMigrationHostNetworkException(
            'Preparation of migration host network failed with {0}'.format(
                issue
            )
        ) from issue


def log_network_details():
    """
    Provide detailed information about the current network setup

    The method must be called in an active and online network state to provide
    most useful information about the network interfaces and its setup.
    """
    log = logging.getLogger(Defaults.get_migration_log_name())
    log.info(
        'All Network Interfaces {0}{1}'.format(
            os.linesep, Command.run(
                ['ip', 'a'], raise_on_error=False
            ).output
        )
    )
    log.info(
        'Routing Tables {0}{1}'.format(
            os.linesep, Command.run(
                ['ip', 'r'], raise_on_error=False
            ).output
        )
    )
    log.info(
        'DNS Resolver {0}{1}'.format(
            os.linesep, Command.run(
                ['cat', '/etc/resolv.conf'], raise_on_error=False
            ).output
        )
    )
    bonding_paths = '/proc/net/bonding/bond*'
    if os.path.exists(os.path.dirname(bonding_paths)):
        log.info(
            'Network Bonding {0}{1}'.format(
                os.linesep, Command.run(
                    ['cat', bonding_paths], raise_on_error=False
                ).output
            )
        )


def has_host_resolv_setup(resolv_conf_path):
    if not os.path.exists(resolv_conf_path):
        return False
    with open(resolv_conf_path, 'r') as resolv:
        for line in resolv:
            # check there is useful information in the remaining lines
            if line.startswith('search') or line.startswith('nameserver'):
                return True
    return False
