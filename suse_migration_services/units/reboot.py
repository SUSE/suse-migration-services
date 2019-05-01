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
import yaml

# project
from suse_migration_services.command import Command
from suse_migration_services.logger import log
from suse_migration_services.defaults import Defaults


def main():
    """
    DistMigration reboot with new kernel
    """
    try:
        # Note:
        # After the migration process is finished, the system reboots
        # unless the debug file /etc/sle-migration-service is set.
        log.info(
            'Systemctl Status Information: {0}{1}'.format(
                os.linesep, Command.run(
                    ['systemctl', 'status', '-l', '--all'], raise_on_error=False
                ).output
            )
        )
        if is_debug_mode():
            log.info('Reboot skipped due to debug flag set')
        else:
            log.info('Reboot system: [kexec]')
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


def is_debug_mode():
    """
    Returns True or False depending on debug property of system
    migration config file
    """
    with open(Defaults.get_migration_config_file(), 'r') as config:
        config = yaml.full_load(config)
        is_debug_mode = False
        if 'debug' in config:
            is_debug_mode = config['debug']

        return is_debug_mode
