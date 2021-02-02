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
import logging
import os
import shutil

# project
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger
from suse_migration_services.migration_config import MigrationConfig
from suse_migration_services.command import Command


def main():
    """
    DistMigration post mount actions

    Preserve custom data file(s) e.g udev rules from the system
    to be migrated to the live migration system and activate
    those file changes to become effective
    """
    Logger.setup()
    log = logging.getLogger(Defaults.get_migration_log_name())
    root_path = Defaults.get_system_root_path()

    migration_config = MigrationConfig()
    preserve_info = migration_config.get_preserve_info()
    if preserve_info:
        for _, preserve_files in preserve_info.items():
            for preserve_file in preserve_files:
                target_dir = os.path.dirname(preserve_file)
                source_file = os.path.normpath(
                    os.sep.join([root_path, preserve_file])
                )
                log.info(
                    'Copy file: {0} to: {1}'.format(
                        source_file, target_dir
                    )
                )
                shutil.copy(source_file, target_dir)
        if 'rules' in preserve_info.keys():
            Command.run(
                ['udevadm', 'control', '--reload']
            )
            Command.run(
                ['udevadm', 'trigger', '--type=subsystems', '--action=add']
            )
            Command.run(
                ['udevadm', 'trigger', '--type=devices', '--action=add']
            )
