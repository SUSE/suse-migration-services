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
import logging
import re
from textwrap import dedent

from suse_migration_services.defaults import Defaults
from suse_migration_services.command import Command
from suse_migration_services.migration_target import MigrationTarget

log = logging.getLogger(Defaults.get_migration_log_name())


def root_login(migration_system=False):
    """
    Check whether sshd is enabled and root login is allowed. If so,
    warn user that they might want to enable it back before starting
    the migration.
    """
    if migration_system:
        # Running on migration system does not make sense for this check
        # since there is no chance for user to do anything anyway
        return

    target = MigrationTarget.get_migration_target()
    if not target.get('version').startswith('16'):
        # This check is only necessary for migration to SLE16
        return

    sshd_is_enabled = Command.run(
        ['systemctl', '--quiet', 'is-enabled', 'sshd'],
        raise_on_error=False
    ).returncode == 0  # systemctl return code: 0 - enabled, 1 - disabled
    if not sshd_is_enabled:
        return

    sshd_t_output = Command.run(['sshd', '-T']).output.lower()
    match = re.search('^permitrootlogin (.*)$', sshd_t_output, re.MULTILINE)
    permit_root_login = match.group(1).strip()
    if permit_root_login == 'no':
        # root login already disabled
        return

    message = dedent("""\n
    Root login by ssh will be disabled by default in SLE16.
    You might want to enable it back before starting the migration.
    To do so, create /etc/ssh/sshd_config.d/50-permit-root-login.conf
    with the following content:

    PermitRootLogin yes

    Once the migration is complete, you can install
    openssh-server-config-rootlogin package and remove the previously
    added file.
    """)
    log.warning(message)
