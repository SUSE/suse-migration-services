# Copyright (c) 2025
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
"""Module for checking for CPU architecture support"""
import logging
import os
import platform
import re

from suse_migration_services.defaults import Defaults
from suse_migration_services.command import Command
from suse_migration_services.migration_target import MigrationTarget

log = logging.getLogger(Defaults.get_migration_log_name())


def x86_64_version():
    """Function to check whether current CPU architecture is new enough to support SLE16"""
    target = MigrationTarget.get_migration_target()
    version = target.get('version')

    if not version or not version.startswith('16'):
        # This check is only necessary for migration to SLE16
        return

    os.environ['ZYPP_READONLY_HACK'] = '1'
    zypper_call = Command.run(['zypper', 'system-architecture'])
    arch = zypper_call.output

    if arch.strip().lower() == "x86_64":
        log.error(
            'SLE16 requires x86_64_v2 at minimum. The architecture version '
            'of this system is too old.'
        )


def power10_version():
    """Function to check whether the system has at least POWER10 CPU for SLE16 migration"""
    target = MigrationTarget.get_migration_target()
    version = target.get('version')

    if not version or not version.startswith('16'):
        # This check is only necessary for migration to SLE16
        return

    machine = platform.machine()

    if machine not in ['ppc64', 'ppc64le']:
        return

    try:
        with open('/proc/cpuinfo', 'r') as cpuinfo_file:
            cpuinfo_content = cpuinfo_file.read()

            # Extract POWER generation number from cpuinfo
            power_match = re.search(r'POWER(\d+)', cpuinfo_content)

            if power_match:
                power_generation = int(power_match.group(1))
                if power_generation < 10:
                    log.error(
                        f'SLES 16 requires POWER10 or newer. This system is running '
                        f'POWER{power_generation}, which is not supported for migration to SLES 16.'
                    )
            else:
                log.warning(
                    'Could not detect POWER generation from /proc/cpuinfo. '
                    'Unable to verify POWER10 requirement for SLES 16 migration.'
                )
    except Exception as error:
        log.warning(f'Could not read /proc/cpuinfo to check CPU model: {error}')


def cpu_arch(migration_system=False):
    """Function for CPU architecture related checks"""
    if migration_system:
        # This check must not be called inside of the
        # migration system live iso or container image.
        # It will only be useful on the system to migrate
        # at install time of the Migration package or on
        # manual user invocation of suse-migration-pre-checks
        # prior the actual migration.
        return

    x86_64_version()
    power10_version()
