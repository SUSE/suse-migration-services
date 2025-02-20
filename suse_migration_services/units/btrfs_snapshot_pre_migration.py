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
import os

# project
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger
from suse_migration_services.command import Command
from suse_migration_services.exceptions import (
    DistMigrationBtrfsSnapshotPreMigrationException
)


def main():
    """
    Pre-migration btrfs snapshot creation.

    Creates a backup of the system's data and prepares the file system
    to be suitable for the distribution migration. In case of an error,
    the backup information is used by the zypper migration plugin to
    restore the original product data, such that the plugin's rollback
    mechanism is not negatively influenced.
    """
    Logger.setup()
    log = logging.getLogger(Defaults.get_migration_log_name())
    root_path = Defaults.get_system_root_path()

    try:
        # we want pre snapshot to be created before we installed
        # migration-activation package, if it was installed
        pre_migration_activation_package_snapshot_number = 0
        snapshot_number_base_file = \
            'suse_migration_snapper_btrfs_pre_snapshot_number'
        snapshot_number_file = os.path.normpath(
            os.sep.join(
                [root_path, '/var/cache', snapshot_number_base_file]
            )
        )
        if os.path.isfile(snapshot_number_file):
            with open(snapshot_number_file) as file:
                pre_migration_activation_package_snapshot_number = \
                    file.read().strip()

        # Note: The btrfs snapshot will be created before the
        # mount system setup in order to avoid any potential issues
        # with the new filesystem layout while
        # the migration process proceeds.
        snapper_enabled = Command.run(
            [
                'chroot', root_path, 'snapper', '--no-dbus', 'get-config'
            ], raise_on_error=False
        )
        if snapper_enabled.returncode != 0:
            return

        # Create a new backup before any changes
        snapper_call = Command.run(
            [
                'chroot', root_path, 'snapper',
                '--no-dbus',
                'create',
                '--from', pre_migration_activation_package_snapshot_number,
                '--read-only',
                '--type', 'single',
                '--cleanup-algorithm', 'number',
                '--print-number',
                '--userdata', 'important=yes',
                '--description', 'before offline migration'
            ]
        )
        if snapper_call.returncode == 0:
            pre_snapshot_number = '{}'.format(snapper_call.output)
            with open(
                f'/run/{snapshot_number_base_file}', 'w'
            ) as pre_snapshot_number_file:
                pre_snapshot_number_file.write(pre_snapshot_number)
    except Exception as issue:
        message = 'BTRFS pre-migration snapshot creation failed with {issue}'
        log.error(message)
        raise DistMigrationBtrfsSnapshotPreMigrationException(
            message
        ) from issue
