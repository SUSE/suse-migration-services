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
from suse_migration_services.fstab import Fstab
from suse_migration_services.defaults import Defaults

from suse_migration_services.exceptions import (
    DistMigrationGrubConfigException
)


def main():
    """
    DistMigration update grub to migrated version

    Setup and update grub with content from the migrated system
    """
    root_path = Defaults.get_system_root_path()
    grub_config_file = Defaults.get_grub_config_file()

    dev_mount_point = os.sep.join(
        [root_path, 'dev']
    )
    proc_mount_point = os.sep.join(
        [root_path, 'proc']
    )
    sys_mount_point = os.sep.join(
        [root_path, 'sys']
    )
    try:
        system_mount = Fstab()
        system_mount.read(
            Defaults.get_system_mount_info_file()
        )
        Command.run(
            ['mount', '--bind', '/dev', dev_mount_point]
        )
        system_mount.add_entry(
            '/dev', dev_mount_point
        )
        Command.run(
            ['mount', '--bind', '/proc', proc_mount_point]
        )
        system_mount.add_entry(
            '/proc', proc_mount_point
        )
        Command.run(
            ['mount', '--bind', '/sys', sys_mount_point]
        )
        system_mount.add_entry(
            '/sys', sys_mount_point
        )
        Command.run(
            [
                'chroot', root_path,
                'grub2-mkconfig', '-o', grub_config_file
            ]
        )
        system_mount.export(
            Defaults.get_system_mount_info_file()
        )
    except Exception as issue:
        for entry in system_mount.get_devices():
            Command.run(
                ['umount', entry.mountpoint], raise_on_exception=False
            )
        raise DistMigrationGrubConfigException(
            'Update grub failed with {0}'.format(
                issue
            )
        )
