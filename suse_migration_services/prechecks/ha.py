# Copyright (c) 2025 SUSE Linux LLC.  All rights reserved.
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
"""Call prechecks for HA provided by crmsh"""
import logging
import os
import subprocess

from suse_migration_services.defaults import Defaults


log = logging.getLogger(Defaults.get_migration_log_name())


def check_ha(migration_system=False):
    if migration_system:
        log.info('Skipped checks for high availablity extension in migration system.')
        return
    if not _corosync_conf_exists():
        log.info('corosync.conf not found. Skipped checks for high availablity extension.')
        return
    if not _is_crmsh_capable_to_check():
        log.warning('crmsh version is too old. Skipped checks for high availablity extension.')
        return
    subprocess.run(['crm', 'cluster', 'health', 'sles16', '--local'])


def _corosync_conf_exists():
    return os.access('/etc/corosync/corosync.conf', os.F_OK)


def _is_crmsh_capable_to_check():
    try:
        result = subprocess.run(
            ['crm', 'help', 'cluster', 'health'],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return False
    except Exception as e:
        log.error('Failed to call crmsh: %s', e)
        return False
    return result.returncode == 0 and 'sles16' in result.stdout.decode(errors='replace')
