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
from collections import namedtuple

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
            'fstab_entry_type', ['fstype', 'mountpoint', 'device', 'options']
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
                options = mount_record[3]
                if fstype != 'swap':
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
                                options=options
                            )
                        )
                    else:
                        log.warning(
                            'Device path {0} not found and skipped'.format(
                                device_path
                            )
                        )
                        continue

    def add_entry(self, device, mountpoint, fstype=None, options=None):
        self.fstab.append(
            self.fstab_entry_type(
                fstype=fstype or 'none',
                mountpoint=mountpoint,
                device=device,
                options=options or 'defaults'
            )
        )

    def export(self, filename):
        """
        Export entries, do not apply on boot checks

        :param string filename: path to file name
        """
        with open(filename, 'w') as fstab:
            for entry in self.fstab:
                fstab.write(
                    '{0} {1} {2} {3} 0 0{4}'.format(
                        entry.device, entry.mountpoint,
                        entry.fstype, entry.options,
                        os.linesep
                    )
                )

    def get_devices(self):
        return self.fstab
