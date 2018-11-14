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
from suse_migration_services.fstab import Fstab


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
    root_path = Defaults.get_system_root_path()

    for shared_location in ['/etc/sysconfig/network', '/etc/zypp']:
        Command.run(
            ['umount', shared_location], raise_on_error=False
        )

    fstab_file = os.sep.join(
        [root_path, 'etc', 'fstab']
    )
    if os.path.exists(fstab_file):
        fstab = Fstab(fstab_file)
        for fstab_entry in reversed(fstab.get_devices()):
            if fstab_entry.mountpoint != 'swap':
                mountpoint = ''.join(
                    [root_path, fstab_entry.mountpoint]
                )
                Command.run(
                    ['umount', mountpoint], raise_on_error=False
                )
