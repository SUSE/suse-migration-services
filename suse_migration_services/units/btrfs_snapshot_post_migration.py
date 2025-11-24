# Copyright (c) 2025 SUSE LLC.  All rights reserved.
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

# project
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger
from suse_migration_services.command import Command
from suse_migration_services.exceptions import (
    DistMigrationBtrfsSnapshotPostMigrationException
)


class BtrfsSnapshotPostMigration:
    def __init__(self):
        """
        Post-migration btrfs snapshot creation.

        Creates a image of the system after the distribution migration .
        """
        Logger.setup()
        self.log = logging.getLogger(Defaults.get_migration_log_name())
        self.root_path = Defaults.get_system_root_path()

    def perform(self):
        try:
            self.log.info('Running Post-migration btrfs snapshot creation')
            with open(
                '/run/suse_migration_snapper_btrfs_pre_snapshot_number'
            ) as pre_snapshot_number_file:
                pre_snapshot_number = pre_snapshot_number_file.read().strip()
                if not pre_snapshot_number.isdigit():
                    message = f'Invalid snapshot number: {pre_snapshot_number}'
                    self.log.error(message)
                    raise ValueError(message)

            Command.run(
                [
                    'chroot', self.root_path, 'snapper',
                    '--no-dbus',
                    'create',
                    '--type', 'single',
                    '--read-only',
                    '--cleanup-algorithm', 'number',
                    '--print-number',
                    '--userdata', 'important=yes',
                    '--description', 'after offline migration'
                ]
            )
            self.log.info(
                'BTRFS post-migration snapshot creation completed successfully.'
            )
        except Exception as issue:
            message = 'BTRFS post-migration snapshot creation failed with: {}'
            self.log.error(message.format(issue))
            raise DistMigrationBtrfsSnapshotPostMigrationException(
                message.format(issue)
            )


def main():
    snapshot_post = BtrfsSnapshotPostMigration()
    snapshot_post.perform()
