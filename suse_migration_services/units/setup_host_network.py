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
from suse_migration_services.migration_config import MigrationConfig
from suse_migration_services.path import Path

from suse_migration_services.exceptions import DistMigrationHostNetworkException


class SetupHostNetwork:
    def __init__(self):
        """
        DistMigration activate host network setup

        Setup and activate the network as it is setup on the host
        to become migrated. This includes the import of the network
        configuration from the migration host
        """
        Logger.setup()
        self.log = logging.getLogger(Defaults.get_migration_log_name())
        self.root_path = Defaults.get_system_root_path()

    def perform(self, container):
        system_mount = Fstab()
        system_mount.read(Defaults.get_system_mount_info_file())

        sysconfig_network_providers = os.sep.join(
            [self.root_path, 'etc', 'sysconfig', 'network', 'providers']
        )
        sysconfig_network_setup = os.sep.join([self.root_path, 'etc', 'sysconfig', 'network', '*'])
        etc_network_manager = os.sep.join([self.root_path, 'etc', 'NetworkManager'])
        usr_lib_network_manager = os.sep.join([self.root_path, 'usr', 'lib', 'NetworkManager'])
        network_manager_service = os.sep.join(
            [
                self.root_path,
                'etc',
                'systemd',
                'system',
                'network-online.target.wants',
                'NetworkManager-wait-online.service',
            ]
        )
        wicked_service = os.sep.join(
            [
                self.root_path,
                'etc',
                'systemd',
                'system',
                'network-online.target.wants',
                'wicked.service',
            ]
        )
        try:
            self.log.info('Running setup host network service')
            if os.path.islink(network_manager_service):
                Path.create('/etc/NetworkManager')
                Path.create('/usr/lib/NetworkManager')
                Command.run(['mount', '--bind', etc_network_manager, '/etc/NetworkManager'])
                Command.run(['mount', '--bind', usr_lib_network_manager, '/usr/lib/NetworkManager'])
                system_mount.add_entry(etc_network_manager, '/etc/NetworkManager')
                system_mount.add_entry(usr_lib_network_manager, '/usr/lib/NetworkManager')

            if os.path.exists(sysconfig_network_providers):
                Command.run(
                    [
                        'mount',
                        '--bind',
                        sysconfig_network_providers,
                        '/etc/sysconfig/network/providers',
                    ]
                )
                system_mount.add_entry(
                    sysconfig_network_providers, '/etc/sysconfig/network/providers'
                )
                for network_setup in glob.glob(sysconfig_network_setup):
                    if os.path.isfile(network_setup):
                        shutil.copy(network_setup, '/etc/sysconfig/network')
            if not container:
                action = 'reload'
                if os.path.islink(network_manager_service):
                    action = 'restart'
                Command.run(['systemctl', action, 'network'])
                if os.path.islink(network_manager_service):
                    # wait for NetworkManager to be online
                    Command.run(['nm-online', '-q'])
            if os.path.islink(wicked_service):
                self.wicked2nm_migrate(activate_connections=False if container else True)
            system_mount.export(Defaults.get_system_mount_info_file())
            if container:
                Command.run(['systemctl', 'stop', 'NetworkManager'])
        except Exception as issue:
            message = 'Preparation of migration host network failed with {}'
            self.log.error(message.format(issue))
            raise DistMigrationHostNetworkException(message.format(issue))

    def log_network_details(self):
        """
        Provide detailed information about the current network setup

        The method must be called in an active and online network state
        to provide most useful information about the network interfaces
        and its setup.
        """
        self.log.info(
            'All Network Interfaces {0}{1}'.format(
                os.linesep, Command.run(['ip', 'a'], raise_on_error=False).output
            )
        )
        self.log.info(
            'Routing Tables {0}{1}'.format(
                os.linesep, Command.run(['ip', 'r'], raise_on_error=False).output
            )
        )
        self.log.info(
            'DNS Resolver {0}{1}'.format(
                os.linesep, Command.run(['cat', '/etc/resolv.conf'], raise_on_error=False).output
            )
        )
        bonding_paths = '/proc/net/bonding/bond*'
        if os.path.exists(os.path.dirname(bonding_paths)):
            self.log.info(
                'Network Bonding {0}{1}'.format(
                    os.linesep, Command.run(['cat', bonding_paths], raise_on_error=False).output
                )
            )

    def wicked2nm_migrate(self, activate_connections=True):
        """
        Migrate from wicked to NetworkManager

        Requires the `wicked show-config` xml along with netconfig files to be
        present at `/var/cache/wicked_config`. These files are supposed to be
        generated by rpm scriptlets. If the files aren't present this part is
        skipped.
        """
        self.log.info('Running wicked2nm host network migration')

        wicked_config_path = os.sep.join([self.root_path, 'var/cache/wicked_config'])
        netconf_dir_path = os.sep.join([self.root_path, 'etc/sysconfig/network'])
        migration_config = MigrationConfig()
        net_info = migration_config.get_network_info()
        if not os.path.exists(os.sep.join([wicked_config_path, 'config.xml'])):
            self.log.info('No wicked config present, skipping wicked2nm.')
            return
        if (
            Command.run(['rpm', '--query', '--quiet', 'wicked2nm'], raise_on_error=False).returncode
            != 0
        ):
            self.log.info('No wicked2nm present, skipping wicked2nm.')
            return
        if (
            Command.run(
                ['rpm', '--query', '--quiet', 'NetworkManager-config-server'], raise_on_error=False
            ).returncode
            != 0
        ):
            self.log.info('No NetworkManager-config-server present, skipping wicked2nm')
            return

        wicked2nm_cmd = ['wicked2nm', 'migrate', '--netconfig-base-dir', netconf_dir_path]
        if activate_connections:
            wicked2nm_cmd.append('--activate-connections')
        wicked2nm_cmd.append(os.sep.join([wicked_config_path, 'config.xml']))
        if (
            net_info
            and 'wicked2nm-continue-migration' in net_info
            and net_info['wicked2nm-continue-migration']
        ):
            self.log.info('Ignoring wicked2nm warnings')
            wicked2nm_cmd = wicked2nm_cmd + ['--continue-migration']
        try:
            Command.run(wicked2nm_cmd)
            # Wait for NetworkManager online to fix dhcp race condition
            Command.run(['nm-online', '-q'])
        except Exception as issue:
            wicked2nm_cmd = [
                'wicked2nm',
                'show',
                '--netconfig-base-dir',
                netconf_dir_path,
                os.sep.join([wicked_config_path, 'config.xml']),
            ]
            self.log.info(
                'wicked2nm config {0}{1}'.format(
                    os.linesep, Command.run(wicked2nm_cmd, raise_on_error=False).output
                )
            )
            self.log_network_details()
            raise DistMigrationHostNetworkException(
                'Migration from wicked to NetworkManager failed with {}'.format(issue)
            )


def main(container=False):
    host_network = SetupHostNetwork()
    host_network.perform(container)


def container():
    """
    DistMigration setup host network setup when running in container

    Setup network needed for the migration when running a
    container based migration process. The DMS uses the host
    networking model, as such the network is already there but
    preparations to move from one network technology to another
    might still be required
    """
    main(container=True)
