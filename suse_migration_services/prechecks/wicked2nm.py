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
import logging
import os
import shutil

from tempfile import NamedTemporaryFile

from suse_migration_services.defaults import Defaults
from suse_migration_services.command import Command

log = logging.getLogger(Defaults.get_migration_log_name())


def check_wicked2nm(migration_system=False):
    """
    Run wicked2nm in dry run mode to check if a migration from
    a wicked based network setup to NetworkManager is possible
    """
    wicked_config_path = '/var/cache/wicked_config'
    wicked_config = os.sep.join(
        [wicked_config_path, 'config.xml']
    )
    if migration_system:
        # This pre-check should not run during migration
        # The actual wicked2nm call to perform the migration
        # happens in the setup_host_network service
        return

    if not shutil.which('wicked2nm') or not shutil.which('wicked'):
        log.info('No wicked setup available. Skipping wicked2nm check.')
        return

    temp_wicked_config = NamedTemporaryFile()
    wicked2nm = [
        'wicked2nm', 'migrate', '--dry-run'
    ]
    if not os.path.isfile(wicked_config):
        # There is no cached wicked config.xml on the system
        # Let's produce the config from the running wicked instance
        # and store it temporary
        wicked_config_output = Command.run(
            ['wicked', 'show-config']
        ).output
        with open(temp_wicked_config.name, 'w') as config:
            config.write(wicked_config_output)
        wicked_config = temp_wicked_config.name
    else:
        # There is a wicked config active, use the standard
        # system netconfig information with this network setup
        wicked2nm += [
            '--netconfig-base-dir', '/etc/sysconfig/network'
        ]
    wicked2nm.append(wicked_config)
    wicked2nm_result = Command.run(
        wicked2nm, raise_on_error=False
    )
    if wicked2nm_result.returncode != 0:
        log.warning('wicked2nm failed with:')
        for relevant_error in wicked2nm_result.error.split(os.linesep):
            if 'WARN' in relevant_error:
                log.warning(relevant_error)
        log.warning(
            'To ignore the warning(s) set: {} in: {}'.format(
                'wicked2nm-continue-migration: true',
                Defaults.get_migration_host_config_file()
            )
        )
