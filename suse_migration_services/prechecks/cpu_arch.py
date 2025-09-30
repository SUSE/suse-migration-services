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

from suse_migration_services.defaults import Defaults
from suse_migration_services.command import Command
from suse_migration_services.migration_target import MigrationTarget


def x86_64_version():
    """Function to check whether current CPU architecture is new enough to support SLE16"""
    target = MigrationTarget.get_migration_target()

    if target.get('version') != '16.0':
        # This check is only necessary for migration to SLE16
        return

    log = logging.getLogger(Defaults.get_migration_log_name())
    os.environ['ZYPP_READONLY_HACK'] = '1'
    zypper_call = Command.run(['zypper', 'system-architecture'])
    arch = zypper_call.output

    if arch.strip().lower() == "x86_64":
        log.error(
            'SLE16 requires x86_64_v2 at minimum. The architecture version '
            'of this system is too old.'
        )


def cpu_arch():
    """Function for CPU architecture related checks"""
    x86_64_version()
