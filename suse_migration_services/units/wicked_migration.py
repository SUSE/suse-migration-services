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

# project
from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger

from suse_migration_services.exceptions import (
    DistMigrationWickedMigrationException
)


def main():
    """
    DistMigration migrate from wicked to NetworkManager
    """
    Logger.setup()
    log = logging.getLogger(Defaults.get_migration_log_name())
    root_path = Defaults.get_system_root_path()

    try:
        log.info('Running wicked to NetworkManager migration')
        log.info(
            'Change systemd network.service symlink '
            'from wicked.service to NetworkManager'
        )

        Command.run(
            [
                'systemctl', '--root', root_path, 'enable',
                '--force', 'NetworkManager.service'
            ]
        )

        log.info('Disable wicked service completely')
        Command.run(
            [
                'systemctl', '--root', root_path, 'mask',
                'wicked.service'
            ]
        )
    except Exception as issue:
        message = 'wicked to NetworkManager migration failed with {}'.format(
            issue
        )
        log.error(message)
        raise DistMigrationWickedMigrationException(message)
