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
from suse_migration_services.drop_components import DropComponents

from suse_migration_services.exceptions import (
    DistMigrationAppArmorMigrationException
)


class ApparmorToSelinux(DropComponents):
    def __init__(self):
        """
        DistMigration migrate from apparmor to SELinux

        Setup grub to use selinux instead of apparmor
        """
        Logger.setup()
        self.log = logging.getLogger(Defaults.get_migration_log_name())
        self.root_path = Defaults.get_system_root_path()
        super().__init__()

    def perform(self):
        try:
            self.log.info('Running AppArmor to SELinux migration')
            self.log.info(
                'Replace occurrence of security=apparmor with '
                'security=selinux in /etc/default/grub'
            )
            pattern = r"security=apparmor\b"
            with fileinput.input(
                Defaults.get_grub_default_file(), inplace=True
            ) as finput:
                for line in finput:
                    print(re.sub(pattern, "security=selinux", line), end='')

            self.log.info('Installing patterns-base-selinux')
            # selinux migration is allowed to fail, it can be fixed
            # after the migration
            zypper_call = Zypper.install(
                'patterns-base-selinux',
                extra_args=['--no-recommends'],
                raise_on_error=False, chroot=self.root_path
            )
            zypper_call.log_if_failed(self.log)
        except Exception as issue:
            message = 'Apparmor to SELinux migration failed with {0}'.format(
                issue
            )
            self.log.error(message)
            raise DistMigrationAppArmorMigrationException(message)


def main():
    system_security = ApparmorToSelinux()
    system_security.perform()
