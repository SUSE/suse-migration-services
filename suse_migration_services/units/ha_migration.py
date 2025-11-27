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
import logging
import os

from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger
from suse_migration_services.exceptions import DistMigrationException


class HighAvailabilityExtension:
    def __init__(self):
        """
        Migration for high availability extension
        """
        Logger.setup()
        self.log = logging.getLogger(Defaults.get_migration_log_name())
        self.root_path = Defaults.get_system_root_path()

    def perform(self):
        self.log.info('Running migration for high availability extension')
        self.log.info('chroot to %s', self.root_path)

        os.chroot(self.root_path)

        if not self._corosync_conf_exists():
            self.log.info(
                'corosync.conf not found. Skipped HA extension migration.'
            )
            return
        try:
            Command.run(
                [
                    'crm', 'cluster', 'health', 'sles16', '--local', '--fix',
                ]
            )
        except Exception as issue:
            message = 'Migration for high availability failed with: {}'
            self.log.error(message.format(issue))
            raise DistMigrationException(message.format(issue))

    def _corosync_conf_exists(self):
        return os.access('/etc/corosync/corosync.conf', os.F_OK)


def main():
    ha_setup = HighAvailabilityExtension()
    ha_setup.perform()
