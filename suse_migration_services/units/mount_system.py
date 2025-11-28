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
import re
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


class MountSystem:
    def __init__(self):
        """
        DistMigration mount system to upgrade

        Searches on all partitions for a fstab file. The first
        fstab file found is used as the system to upgrade.
        Filesystems relevant for an upgrade process are read from
        that fstab in order and mounted such that the system rootfs
        is available for a zypper based migration process.
        """
        Logger.setup()
        self.log = logging.getLogger(Defaults.get_migration_log_name())
        self.root_path = Defaults.get_system_root_path()

    def perform(self):
        Path.create(self.root_path)
        self.log.info('Running mount system service')

        if self.is_mounted(self.root_path):
            # root_path is already a mount point, better not continue
            # The condition is not handled as an error because the
            # existing mount point under this service created root_path
            # is considered to represent the system to upgrade and
            # not something else. Thus if already mounted, let's use
            # what is there.
            return

        self.log.info('Mount system service: {0} is mounted'.format(
            self.root_path)
        )
        # Check if booted via loopback grub
        isoscan_loop_mount = '/run/initramfs/isoscan'
        if self.is_mounted(isoscan_loop_mount):
            # The system to become migrated was booted via a grub
            # loopback menuentry. This means the disk is blocked by
            # that readonly loopback mount and needs to be
            # remounted for read write access first
            self.log.info(
                'Mount system service: {0} is mounted'
                .format(isoscan_loop_mount)
            )
            Command.run(
                ['mount', '-o', 'remount,rw', isoscan_loop_mount]
            )

        self.activate_lvm()

        self.mount_system(
            self.read_system_fstab()
        )

        migration_config = MigrationConfig()
        migration_config.update_migration_config_file()
        self.log.info(
            'Config file content:\n{content}\n'.format(
                content=migration_config.get_migration_config_file_content()
            )
        )

    def get_uuid(self, device):
        """
        Retrieve UUID from block device
        """
        blkid_result = Command.run(
            ['blkid', device, '-s', 'UUID', '-o', 'value'],
            raise_on_error=False
        )
        return blkid_result.output.strip(os.linesep) if blkid_result else ''

    def activate_lvm(self):
        lsblk_call = Command.run(
            ['lsblk', '-p', '-n', '-r', '-o', 'NAME,TYPE']
        )
        for entry in lsblk_call.output.split(os.linesep):
            block_record = entry.split()
            if len(block_record) >= 2:
                block_type = block_record[1]
                if block_type == 'lvm':
                    self.log.info(
                        'LVM managed block device(s) found, activating LVM'
                    )
                    Command.run(['vgchange', '-a', 'y'])
                    return

    def get_target_root(self):
        """
        Read the migration_target information from the kernel cmdline
        and provide the associated device name. The migration_target
        information was placed to the cmdline by the DMS grub boot
        menu entry of by the DMS run_migration kexec cmdline parameter
        """
        try:
            with open('/proc/cmdline') as cmdline_fd:
                cmdline = cmdline_fd.read()
            match = re.search(r'migration_target=([\w-]+)', cmdline)
            if match:
                migration_rootfs_uuid = match.group(1)
                lsblk_call = Command.run(
                    ['lsblk', '-p', '-n', '-r', '-o', 'NAME,TYPE']
                )
                considered_block_types = ['part', 'raid', 'lvm']
                for entry in lsblk_call.output.split(os.linesep):
                    block_record = entry.split()
                    if len(block_record) >= 2:
                        block_type = block_record[1]
                        if block_type in considered_block_types:
                            device = block_record[0]
                            uuid = self.get_uuid(device)
                            if uuid == migration_rootfs_uuid:
                                return device
            # nothing was found
            raise DistMigrationSystemMountException(
                'no match for migration_target= in cmdline'
            )
        except Exception as issue:
            message = 'Failed to find target disk: {0}'.format(issue)
            self.log.error(message)
            raise DistMigrationSystemMountException(
                message
            )

    def read_system_fstab(self):
        self.log.info('Reading fstab from DMS selected target disk')
        migration_target_root = self.get_target_root()
        try:
            self.log.info(
                'Lookup for fstab on {0}'.format(migration_target_root)
            )
            Command.run(
                ['mount', migration_target_root, self.root_path]
            )
            fstab_file = os.sep.join(
                [self.root_path, 'etc', 'fstab']
            )
            if os.path.isfile(fstab_file):
                self.log.info(
                    'Found {0} on {1}'.format(fstab_file, migration_target_root)
                )
                fstab = Fstab()
                fstab.read(fstab_file)
                return fstab
            raise DistMigrationSystemNotFoundException(
                'Could not find system with fstab on {0}'.format(
                    migration_target_root
                )
            )
        except Exception as issue:
            Command.run(
                ['umount', self.root_path], raise_on_error=False
            )
            raise DistMigrationSystemNotFoundException(
                'Reading fstab failed with: {}'.format(issue)
            )

    def mount_system(self, fstab):
        self.log.info('Mount system in {0}'.format(self.root_path))
        system_mount = Fstab()
        explicit_mount_points = {
            'devtmpfs': os.sep.join([self.root_path, 'dev']),
            'proc': os.sep.join([self.root_path, 'proc']),
            'sysfs': os.sep.join([self.root_path, 'sys'])
        }
        try:
            for fstab_entry in fstab.get_devices():
                mountpoint = ''.join(
                    [self.root_path, fstab_entry.mountpoint]
                )
                if mountpoint not in explicit_mount_points.values():
                    if fstab_entry.eligible_for_mount:
                        self.log.info('Mounting {0}'.format(mountpoint))
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

            self.log.info(
                'Mounting kernel file systems inside {0}'.format(self.root_path)
            )
            for mount_type, mount_point in explicit_mount_points.items():
                Command.run(
                    ['mount', '-t', mount_type, mount_type, mount_point]
                )
                system_mount.add_entry(
                    mount_type, mount_point
                )
            self.log.info(
                'Bind mount subdirectories from /run inside chroot {0}'.format(
                    self.root_path
                )
            )
            os.makedirs(
                os.sep.join([self.root_path, 'run', 'NetworkManager']),
                exist_ok=True
            )
            Command.run(
                [
                    'mount', '-o', 'bind', '/run/NetworkManager',
                    os.sep.join([self.root_path, 'run', 'NetworkManager'])
                ]
            )
            os.makedirs(
                os.sep.join([self.root_path, 'run', 'netconfig']),
                exist_ok=True
            )
            Command.run(
                [
                    'mount', '-o', 'bind', '/run/netconfig',
                    os.sep.join([self.root_path, 'run', 'netconfig'])
                ]
            )
        except Exception as issue:
            self.log.error(
                'Mounting system for upgrade failed with {0}'.format(issue)
            )
            raise DistMigrationSystemMountException(
                'Mounting system for upgrade failed with {0}'.format(issue)
            )
        system_mount.export(
            Defaults.get_system_mount_info_file()
        )

    def is_mounted(self, mount_point):
        self.log.info('Checking {0} is mounted'.format(mount_point))
        # a bind mount is neither a device nor an inode.
        # Thus, ismount will return False for those, as
        # it is very unlikely that a bind mount is used in fstab,
        # that case is not handled
        return os.path.ismount(mount_point)


def main():
    mount_os = MountSystem()
    mount_os.perform()
