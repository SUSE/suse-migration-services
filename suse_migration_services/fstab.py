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
from collections import namedtuple


class Fstab(object):
    """
    **Reading fstab values**
    """
    def __init__(self, filename):
        """
        Import specified fstab file

        :param string filename: path to a fstab file
        """
        fstab_entry_type = namedtuple(
            'fstab_entry_type', ['mountpoint', 'device', 'options']
        )
        self.fstab = []
        with open(filename) as fstab:
            for line in fstab.readlines():
                mount_record = line.split()
                device = mount_record[0]
                mountpoint = mount_record[1]
                options = mount_record[3]
                if device.startswith('UUID'):
                    device_path = ''.join(
                        ['/dev/disk/by-uuid/', device.split('=')[1]]
                    )
                elif device.startswith('LABEL'):
                    device_path = ''.join(
                        ['/dev/disk/by-label/', device.split('=')[1]]
                    )
                else:
                    device_path = device
                self.fstab.append(
                    fstab_entry_type(
                        mountpoint=mountpoint,
                        device=device_path,
                        options=options
                    )
                )

    def get_devices(self):
        return self.fstab
