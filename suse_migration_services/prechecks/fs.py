# Copyright (c) 2022
#
# SUSE Linux LLC.  All rights reserved.
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
"""Module for checking for encrypted filesystems"""
import logging

from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults
from suse_migration_services.fstab import Fstab


def encryption(migration_system=False):
    """Function to check for encrypted filesystemsssss"""
    log = logging.getLogger(Defaults.get_migration_log_name())
    fstab = Fstab()
    fstab_path = '/etc/fstab'
    if migration_system:
        fstab_path = Defaults.get_system_root_path() + fstab_path
    fstab.read(fstab_path)
    fstab_entries = fstab.get_devices()

    for fstab_entry in fstab_entries:
        result = Command.run(
            ["blkid", "-s", "TYPE", "-o", "value", fstab_entry.device]
        )
        if result.returncode == 0:
            if 'LUKS' in result.output:
                log.warning(
                    'There are encrypted filesystems: {}, this may be an '
                    'issue when migrating'.format(fstab_entry.device)
                )
