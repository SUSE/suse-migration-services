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
import os

# project
from suse_migration_services.path import Path
from suse_migration_services.command import Command
from suse_migration_services.logger import log
from suse_migration_services.defaults import Defaults


def main():
    """
    DistMigration reboot with new kernel
    """
    debug_file = os.sep + Defaults.get_system_migration_debug_file()

    try:
        # Note:
        # After the migration process is finished, the system reboots
        # unless the debug file /etc/sle-migration-service is set.
        if os.path.exists(debug_file):
            log.info('Reboot skipped due to debug flag set')
        else:
            log.info('Reboot system: [kexec]')
            Path.wipe(debug_file)
            Command.run(
                ['kexec', '--exec']
            )
    except Exception:
        # Uhh, we don't want to be here, but we also don't
        # want to be stuck in the migration live system.
        # Keep fingers crossed:
        log.warning('Reboot system: [Force Reboot]')
        Command.run(
            ['reboot', '-f']
        )
