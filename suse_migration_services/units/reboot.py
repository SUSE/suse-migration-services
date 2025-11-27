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
import os

# project
from suse_migration_services.command import Command
from suse_migration_services.logger import Logger
from suse_migration_services.defaults import Defaults
from suse_migration_services.fstab import Fstab
from suse_migration_services.migration_config import MigrationConfig


class Reboot:
    def __init__(self):
        """
        DistMigration reboot with new kernel

        After the migration process is finished, the system reboots
        unless the debug option is set.

        Before reboot a reverse umount of the filesystems that got mounted
        by the mount_system service is performed and thus releases the
        upgraded system from the migration host. If for whatever reason
        a filesystem is busy and can't be umounted, this condition is not
        handled as an error. The reason is that the cleanup should not
        prevent us from continuing with the reboot process. The risk on
        reboot of the migration host with a potential active mount
        is something we accept
        """
        Logger.setup()
        self.log = logging.getLogger(Defaults.get_migration_log_name())

    def perform(self):
        self.log.info('Running reboot service')
        try:
            migration_config = MigrationConfig()
            migration_config.update_migration_config_file()
            self.log.info(
                'Config file content:\n{content}\n'. format(
                    content=migration_config.get_migration_config_file_content()
                )
            )
            # stop console dialog log. The service holds a busy state
            # on system-root and stands in our way in case of debug
            # mode because it grabs the master console in/output
            Command.run(
                ['systemctl', 'stop', 'suse-migration-console-log'],
                raise_on_error=False
            )
            if migration_config.is_debug_requested():
                self.log.info('Reboot skipped due to debug flag set')
            else:
                self.log.info('Umounting system')
                system_mount = Fstab()
                system_mount.read(
                    Defaults.get_system_mount_info_file()
                )
                for mount in reversed(system_mount.get_devices()):
                    self.log.info(
                        'Umounting {0}: {1}'.format(
                            mount.mountpoint, Command.run(
                                ['umount', '--lazy', mount.mountpoint],
                                raise_on_error=False
                            )
                        )
                    )
                if not migration_config.is_soft_reboot_requested():
                    restart_system = 'reboot'
                else:
                    restart_system = 'kexec'
                self.log.info(
                    'Reboot system: {0}{1}'.format(
                        os.linesep, Command.run(
                            ['systemctl', restart_system]
                        )
                    )
                )
        except Exception:
            # Uhh, we don't want to be here, but we also don't
            # want to be stuck in the migration live system.
            # Keep fingers crossed:
            self.log.warning('Reboot system: [Force Reboot]')
            Command.run(
                ['systemctl', '--force', 'reboot']
            )


def main():
    reboot = Reboot()
    reboot.perform()
