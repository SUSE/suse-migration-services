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

    MigrationConfig().update_migration_config_file()


def read_system_fstab(root_path):
    log = logging.getLogger(Defaults.get_migration_log_name())
    log.info('Reading fstab from associated disks')
    lsblk_call = Command.run(
        ['lsblk', '-p', '-n', '-r', '-o', 'NAME,TYPE']
    )
    for entry in lsblk_call.output.split(os.linesep):
        block_record = entry.split()
        if len(block_record) >= 2:
            block_type = block_record[1]
            if block_type == 'part' or block_type.startswith('raid'):
                try:
                    Command.run(
                        ['mount', block_record[0], root_path],
                        raise_on_error=False
                    )
                    fstab_file = os.sep.join([root_path, 'etc', 'fstab'])
                    if os.path.exists(fstab_file):
                        fstab = Fstab()
                        fstab.read(fstab_file)
                        return(fstab, lsblk_call.output)
                finally:
                    log.info('Umount {0}'.format(root_path))
                    Command.run(
                        ['umount', root_path],
                        raise_on_error=False
                    )
    return(None, lsblk_call.output)


def mount_system(root_path, fstab):
    log = logging.getLogger(Defaults.get_migration_log_name())
    log.info('Mount system in {0}'.format(root_path))
    system_mount = Fstab()
    try:
        for fstab_entry in fstab.get_devices():
            mountpoint = ''.join(
                [root_path, fstab_entry.mountpoint]
            )
            log.info('Mounting {0}'.format(mountpoint))
            Command.run(
                [
                    'mount', '-o', fstab_entry.options,
                    fstab_entry.device, mountpoint
                ]
            )
            system_mount.add_entry(
                fstab_entry.device, mountpoint, fstab_entry.fstype
            )

        log.info('Mounting kernel file systems inside {0}'.format(root_path))
        dev_mount_point = os.sep.join(
            [root_path, 'dev']
        )
        Command.run(
            ['mount', '-t', 'devtmpfs', 'devtmpfs', dev_mount_point]
        )
        system_mount.add_entry(
            'devtmpfs', dev_mount_point
        )
        proc_mount_point = os.sep.join(
            [root_path, 'proc']
        )
        Command.run(
            ['mount', '-t', 'proc', 'proc', proc_mount_point]
        )
        system_mount.add_entry(
            '/proc', proc_mount_point
        )
        sys_mount_point = os.sep.join(
            [root_path, 'sys']
        )
        Command.run(
            ['mount', '-t', 'sysfs', 'sysfs', sys_mount_point]
        )
        system_mount.add_entry(
            'sysfs', sys_mount_point
        )
    except Exception as issue:
        log.error(
            'Mounting system for upgrade failed with {0}'.format(issue)
        )
        for entry in reversed(system_mount.get_devices()):
            Command.run(['umount', entry.mountpoint])
        raise DistMigrationSystemMountException(
            'Mounting system for upgrade failed with {0}'.format(issue)
        )
    system_mount.export(
        Defaults.get_system_mount_info_file()
    )


def is_mounted(mount_point):
    log = logging.getLogger(Defaults.get_migration_log_name())
    log.info('Checking {0} is mounted'.format(mount_point))
    if os.path.exists(mount_point):
        mountpoint_call = Command.run(
            ['mountpoint', '-q', mount_point], raise_on_error=False
        )
        if mountpoint_call.returncode == 0:
            return True
    return False
