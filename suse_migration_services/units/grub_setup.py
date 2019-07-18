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

# project
from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import log

from suse_migration_services.exceptions import (
    DistMigrationGrubConfigException
)


def main():
    """
    DistMigration update grub to migrated version

    Setup and update grub with content from the migrated system
    Uninstall live migration packages such that they are no longer
    part of the now migrated system.
    """
    root_path = Defaults.get_system_root_path()
    grub_config_file = Defaults.get_grub_config_file()

    try:
        log.info('Running grub setup service')
        migration_packages = [
            'SLE*-Migration',
            'suse-migration-*-activation'
        ]
        log.info(
            'Uninstalling migration: {0}{1}'.format(
                os.linesep, Command.run(
                    [
                        'chroot', root_path, 'zypper',
                        '--non-interactive', '--no-gpg-checks',
                        'remove'
                    ] + migration_packages, raise_on_error=False
                ).output
            )
        )
        log.info(
            'Creating new grub menu: {0}{1}'.format(
                os.linesep, Command.run(
                    [
                        'chroot', root_path, 'grub2-mkconfig', '-o',
                        '{0}{1}'.format(os.sep, grub_config_file)
                    ]
                ).error
            )
        )
    except Exception as issue:
        message = 'Update grub failed with {0}'.format(issue)
        log.error(message)
        raise DistMigrationGrubConfigException(message)
