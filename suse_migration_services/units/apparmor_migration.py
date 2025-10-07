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
import fileinput
import re

# project
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger
from suse_migration_services.zypper import Zypper

from suse_migration_services.exceptions import (
    DistMigrationAppArmorMigrationException
)


def main():
    """
    DistMigration migrate from apparmor to SELinux

    Setup grub to use selinux instead of apparmor
    """
    Logger.setup()
    log = logging.getLogger(Defaults.get_migration_log_name())

    root_path = Defaults.get_system_root_path()

    try:
        log.info('Running AppArmor to SELinux migration')
        log.info(
            'Replace occurrence of security=apparmor with '
            'security=selinux in /etc/default/grub'
        )
        pattern = r"security=apparmor\b"
        with fileinput.input(
            Defaults.get_grub_default_file(), inplace=True
        ) as finput:
            for line in finput:
                print(re.sub(pattern, "security=selinux", line), end='')

        log.info('Installing patterns-base-selinux')
        # selinux migration is allowed to fail, it can be fixed
        # after the migration
        Zypper.run(
            [
                '--no-cd',
                '--non-interactive',
                '--gpg-auto-import-keys',
                '--root', root_path,
                'install',
                '--auto-agree-with-licenses',
                '--allow-vendor-change',
                '--download', 'in-advance',
                '--replacefiles',
                '--allow-downgrade',
                '--no-recommends',
                'patterns-base-selinux'
            ], raise_on_error=False
        )
    except Exception as issue:
        message = 'Apparmor to SELinux migration failed with {0}'.format(issue)
        log.error(message)
        raise DistMigrationAppArmorMigrationException(message)
