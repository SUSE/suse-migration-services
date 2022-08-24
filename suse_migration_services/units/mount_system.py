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
from suse_migration_services.defaults import Defaults
from suse_migration_services.fstab import Fstab
from suse_migration_services.path import Path
from suse_migration_services.logger import Logger
from suse_migration_services.migration_config import MigrationConfig

from suse_migration_services.exceptions import (
    DistMigrationSystemNotFoundException,
    DistMigrationSystemMountException
)


def main():
    """
    DistMigration mount system to upgrade

    Searches on all partitions for a fstab file. The first
    fstab file found is used as the system to upgrade.
    Filesystems relevant for an upgrade process are read from
    that fstab in order and mounted such that the system rootfs
    is available for a zypper based migration process.
    """
    Logger.setup()
    log = logging.getLogger(Defaults.get_migration_log_name())
    root_path = Defaults.get_system_root_path()
    Path.create(root_path)
    log.info('Running mount system service')

    if is_mounted(root_path):
        # root_path is already a mount point, better not continue
        # The condition is not handled as an error because the
        # existing mount point under this service created root_path
        # is considered to represent the system to upgrade and
        # not something else. Thus if already mounted, let's use
        # what is there.
        return

    log.info('Mount system service: {0} is mounted'.format(root_path))
    # Check if booted via loopback grub
    isoscan_loop_mount = '/run/initramfs/isoscan'
    if is_mounted(isoscan_loop_mount):
        # The system to become migrated was booted via a grub
        # loopback menuentry. This means the disk is blocked by
        # that readonly loopback mount and needs to be
        # remounted for read write access first
        log.info(
            'Mount system service: {0} is mounted'
            .format(isoscan_loop_mount)
        )
        Command.run(
            ['mount', '-o', 'remount,rw', isoscan_loop_mount]
        )

    fstab, storage_info = read_system_fstab(root_path)
    if not fstab:
        log.error(
            'Could not find system in fstab on {0}'.format(
                storage_info
            )
        )
        raise DistMigrationSystemNotFoundException(
            'Could not find system with fstab on {0}'.format(
                storage_info
            )
        )

    mount_system(root_path, fstab)

    migration_config = MigrationConfig()
    migration_config.update_migration_config_file()
    log.info(
        'Config file content:\n{content}\n'. format(
            content=migration_config.get_migration_config_file_content()
        )
    )


def read_system_fstab(root_path):
    log = logging.getLogger(Defaults.get_migration_log_name())
    log.info('Reading fstab from associated disks')
    lsblk_call = Command.run(
        ['lsblk', '-p', '-n', '-r', '-o', 'NAME,TYPE']
    )
    considered_block_types = ['part', 'raid', 'lvm']
    considered_block_devices = []
    lvm_managed_block_device_found = False
    for entry in lsblk_call.output.split(os.linesep):
        block_record = entry.split()
        if len(block_record) >= 2:
            block_type = block_record[1]
            if block_type in considered_block_types:
                if block_type == 'lvm':
                    lvm_managed_block_device_found = True
                considered_block_devices.append(
                    block_record[0]
                )

    if lvm_managed_block_device_found:
        log.info('LVM managed block device(s) found, activating volume groups')
        Command.run(['vgchange', '-a', 'y'])

    for block_device in considered_block_devices:
        try:
            log.info('Lookup for fstab on %s ...', block_device)
            Command.run(
                ['mount', block_device, root_path]
            )
            fstab_file = os.sep.join([root_path, 'etc', 'fstab'])
            if os.path.isfile(fstab_file):
                log.info('Found %s on %s ', fstab_file, block_device)
                fstab = Fstab()
                fstab.read(fstab_file)
                return (fstab, lsblk_call.output)
            log.info('No %s found on ', block_device)
            log.info('Umount %s', root_path)
            Command.run(
                ['umount', root_path], raise_on_error=False
            )
        except Exception as issue:
            log.info('Exception on mount of %s: %s', block_device, issue)
    return (None, lsblk_call.output)


def mount_system(root_path, fstab):
    log = logging.getLogger(Defaults.get_migration_log_name())
    log.info('Mount system in {0}'.format(root_path))
    system_mount = Fstab()
    explicit_mount_points = {
        'devtmpfs': os.sep.join([root_path, 'dev']),
        'proc': os.sep.join([root_path, 'proc']),
        'sysfs': os.sep.join([root_path, 'sys'])
    }
    try:
        for fstab_entry in fstab.get_devices():
            mountpoint = ''.join(
                [root_path, fstab_entry.mountpoint]
            )
            if mountpoint not in explicit_mount_points.values():
                if fstab_entry.eligible_for_mount:
                    log.info('Mounting {0}'.format(mountpoint))
                    Command.run(
                        [
                            'mount', '-o', fstab_entry.options,
                            fstab_entry.device, mountpoint
                        ]
                    )
                system_mount.add_entry(
                    fstab_entry.device, mountpoint, fstab_entry.fstype,
                    fstab_entry.eligible_for_mount
                )

        log.info('Mounting kernel file systems inside {0}'.format(root_path))
        for mount_type, mount_point in explicit_mount_points.items():
            Command.run(
                ['mount', '-t', mount_type, mount_type, mount_point]
            )
            system_mount.add_entry(
                mount_type, mount_point
            )
    except Exception as issue:
        log.error(
            'Mounting system for upgrade failed with {0}'.format(issue)
        )
        raise DistMigrationSystemMountException(
            'Mounting system for upgrade failed with {0}'.format(issue)
        )
    system_mount.export(
        Defaults.get_system_mount_info_file()
    )


def is_mounted(mount_point):
    log = logging.getLogger(Defaults.get_migration_log_name())
    log.info('Checking {0} is mounted'.format(mount_point))
    # a bind mount is neither a device nor an inode.
    # Thus, ismount will return False for those, as
    # it is very unlikely that a bind mount is used in fstab,
    # that case is not handled
    return os.path.ismount(mount_point)
