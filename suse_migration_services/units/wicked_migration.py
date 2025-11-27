# Copyright (c) 2025 SUSE Linux LLC.  All rights reserved.
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
import logging
import glob

# project
from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger
from suse_migration_services.drop_components import DropComponents

from suse_migration_services.exceptions import (
    DistMigrationWickedMigrationException
)


class WickedToNetworkManager(DropComponents):
    def __init__(self):
        """
        DistMigration migrate from wicked to NetworkManager
        """
        Logger.setup()
        self.log = logging.getLogger(Defaults.get_migration_log_name())
        self.root_path = Defaults.get_system_root_path()
        super().__init__()

    def perform(self):
        try:
            self.log.info('Running wicked to NetworkManager migration')
            self.log.info('Enabling NetworkManager in migrated system')
            Command.run(
                [
                    'systemctl', '--root', self.root_path, 'enable',
                    '--force', 'NetworkManager.service'
                ]
            )

            self.log.info('Disable wicked service completely')
            Command.run(
                [
                    'systemctl', '--root', self.root_path, 'mask',
                    'wicked.service'
                ]
            )

            self.log.info('Copy connections to migrated system')
            nm_connection_pattern = \
                '/etc/NetworkManager/system-connections/*.nmconnection'
            nm_connections_path = os.path.normpath(
                os.sep.join(
                    [self.root_path, 'etc/NetworkManager/system-connections']
                )
            )
            Command.run(
                ['mkdir', '-p', nm_connections_path]
            )
            for connection in sorted(glob.iglob(nm_connection_pattern)):
                Command.run(
                    ['cp', connection, nm_connections_path]
                )
        except Exception as issue:
            message = 'wicked to NetworkManager migration failed with {}'.format(
                issue
            )
            self.log.error(message)
            raise DistMigrationWickedMigrationException(message)


def main():
    network_migration = WickedToNetworkManager()
    network_migration.perform()
