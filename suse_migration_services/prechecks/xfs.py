# Copyright (c) 2026 SUSE Linux LLC.  All rights reserved.
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
"""Module for checking XFS filesystem version"""
import logging
import re

from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults


def xfs_v4(migration_system=False):
    """Check for XFS v4 root filesystem and warn about potential issues"""
    if migration_system:
        # This check must not be called inside of the
        # migration system live iso or container image.
        # It will only be useful on the system to migrate
        # at install time of the Migration package or on
        # manual user invocation of suse-migration-pre-checks
        # prior the actual migration.
        return

    log = logging.getLogger(Defaults.get_migration_log_name())

    stat_result = Command.run(['stat', '-f', '-c', '%T', '/'])
    if stat_result:
        target_fs = stat_result.output.strip()
        if target_fs != 'xfs':
            return

    xfs_info_result = Command.run(['xfs_info', '/'])

    # Check for v4 filesystem (absence of crc=1 indicates v4)
    # v5 filesystems have: crc=1, finobt=1, sparse=1, rmapbt=0, reflink=1
    # v4 filesystems typically show: crc=0 or no crc field
    output = xfs_info_result.output
    if re.search(r'crc=0\b', output) or 'crc=' not in output:
        log.warning(
            'XFS v4 root filesystem detected. XFS v4 is deprecated and support '
            'will be dropped after September 2030. See the XFS formats chapter '
            'in Storage Administration Guide for details on this issue.'
        )
