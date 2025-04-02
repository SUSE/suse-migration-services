# Copyright (c) 2025 SUSE LLC.  All rights reserved.
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
# along with suse-migration-services. If not, see <http://www.gnu.org/licenses/>#
"""
Module for checking for LTSS
"""
import logging
import os

from suse_migration_services.defaults import Defaults


def check_enabled(migration_system=False):
    """
    Check if LTSS is enabled on the system to migrate.
    It's not supported by SUSE to upgrade to another major
    code stream with LTSS enabled for the current code stream.
    """
    log = logging.getLogger(Defaults.get_migration_log_name())
    system_root = '/'
    if migration_system:
        system_root = Defaults.get_system_root_path()

    ltss_prod = os.path.normpath(
        '{}/etc/products.d/SLES-LTSS.prod'.format(system_root)
    )

    if os.path.exists(ltss_prod):
        log.error(
            'LTSS is enabled and must be disabled for the migration'
        )
