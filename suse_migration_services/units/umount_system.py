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
# project
from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults
from suse_migration_services.fstab import Fstab
from suse_migration_services.logger import log


def main():
    """
    DistMigration umount upgraded system

    Reverse umount the filesystems mounted by the mount_system
    service and thus release the upgraded system from the
    migration host. If for whatever reason a filesystem is busy
    and can't be umounted, this condition is not handled as an
    error. The reason is that the cleanup should not prevent us
    from continuing with the migration process. The risk on
    reboot of the migration host with a potential active mount
    is something we take into account intentionally
    """
    log.info('Running umount system service')
    system_mount = Fstab()
    system_mount.read(
        Defaults.get_system_mount_info_file()
    )
    for mount in reversed(system_mount.get_devices()):
        log.info('Umounting {0}'.format(mount.mountpoint))
        Command.run(
            ['umount', mount.mountpoint], raise_on_error=False
        )
