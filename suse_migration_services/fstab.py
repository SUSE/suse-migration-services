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
from collections import (
    namedtuple, OrderedDict
)

# project
from suse_migration_services.defaults import Defaults

log = logging.getLogger(Defaults.get_migration_log_name())


class Fstab:
    """
    **Managing fstab values**
    """
    def __init__(self):
        self.fstab = []
        self.fstab_entry_type = namedtuple(
            'fstab_entry_type', [
                'fstype', 'mountpoint', 'device', 'options',
                'eligible_for_mount'
            ]
        )

    def read(self, filename):
        """
        Import specified fstab file

        Ignore special filesystems not important in the scope of
        the migration e.g swap

        :param string filename: path to a fstab file
        """
        self.fstab = []
        with open(filename) as fstab:
            for line in fstab.readlines():
                mount_record = line.split()
                if not mount_record or mount_record[0].startswith('#'):
                    continue
                device = mount_record[0]
                mountpoint = mount_record[1]
                fstype = mount_record[2]
                try:
                    options = mount_record[3]
                except IndexError:
                    options = ''
                eligible_for_mount = True
                if fstype != 'swap':
                    if mountpoint == '/':
                        # the main rootfs mountpoint is mounted in an
                        # extra operation and therefore flagged as being
                        # not eligible for a mount operation when read
                        # from this fstab instance
                        eligible_for_mount = False
                    if device.startswith('UUID'):
                        device_path = ''.join(
                            ['/dev/disk/by-uuid/', device.split('=')[1]]
                        )
                    elif device.startswith('LABEL'):
                        device_path = ''.join(
                            ['/dev/disk/by-label/', device.split('=')[1]]
                        )
                    elif device.startswith('PARTUUID'):
                        device_path = ''.join(
                            ['/dev/disk/by-partuuid/', device.split('=')[1]]
                        )
                    else:
                        device_path = device

                    if os.path.exists(device_path):
                        self.fstab.append(
                            self.fstab_entry_type(
                                fstype=fstype,
                                mountpoint=mountpoint,
                                device=device_path,
                                options=options,
                                eligible_for_mount=eligible_for_mount
                            )
                        )
                    else:
                        log.warning(
                            'Device path {0} not found and skipped'.format(
                                device_path
                            )
                        )
                        continue

    def add_entry(
        self, device, mountpoint, fstype=None, options=None,
        eligible_for_mount=True
    ):
        self.fstab.append(
            self.fstab_entry_type(
                fstype=fstype or 'none',
                mountpoint=mountpoint,
                device=device,
                options=options or 'defaults',
                eligible_for_mount=eligible_for_mount
            )
        )

    def export(self, filename):
        """
        Export entries, do not apply on boot checks

        :param string filename: path to file name
        """
        with open(filename, 'w') as fstab:
            for entry in self._get_canonical_mount_list():
                fstab.write(
                    '{0} {1} {2} {3} 0 0{4}'.format(
                        entry.device, entry.mountpoint,
                        entry.fstype, entry.options,
                        os.linesep
                    )
                )

    def get_devices(self):
        return self._get_canonical_mount_list()

    def _get_canonical_mount_list(self):
        """
        Implements hierarchical sorting of mount paths

        :return: list of canonical fstab_entry_type elements

        :rtype: list
        """
        mount_paths = {}
        sorted_fstab = []
        for entry in self.fstab:
            mount_paths[entry.mountpoint] = entry
        for mountpath in Fstab._sort_by_hierarchy(sorted(mount_paths.keys())):
            sorted_fstab.append(mount_paths[mountpath])
        return sorted_fstab

    @staticmethod
    def _sort_by_hierarchy(path_list):
        """
        Sort given list of path names by their hierachy in the tree

        Example:

        .. code:: python

            result = sort_by_hierarchy(['/var/lib', '/var'])

        :param list path_list: list of path names

        :return: hierachy sorted path_list

        :rtype: list
        """
        paths_at_depth = {}
        for path in path_list:
            path_elements = path.split('/')
            path_depth = len(path_elements)
            if path_depth not in paths_at_depth:
                paths_at_depth[path_depth] = []
            paths_at_depth[path_depth].append(path)
        ordered_paths_at_depth = OrderedDict(
            sorted(paths_at_depth.items())
        )
        ordered_paths = []
        for path_depth in ordered_paths_at_depth:
            for path in ordered_paths_at_depth[path_depth]:
                ordered_paths.append(path)
        return ordered_paths
