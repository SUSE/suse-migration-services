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
import logging
import glob
import shutil
import os

# project
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger
from suse_migration_services.command import Command


def main():
    """
    DistMigration ssh access for migration user

    Copy the authoritation key found to the migration user
    directory in order to access through ssh
    """
    Logger.setup()
    log = logging.getLogger(Defaults.get_migration_log_name())
    ssh_keys_glob_paths = Defaults.get_ssh_keys_paths()
    migration_ssh_file = Defaults.get_migration_ssh_file()
    system_ssh_host_keys_glob_path = \
        Defaults.get_system_ssh_host_keys_glob_path()
    sshd_config_path = Defaults.get_system_sshd_config_path()
    try:
        log.info('Running ssh keys service')
        ssh_keys_paths = []
        for glob_path in ssh_keys_glob_paths:
            ssh_keys_paths.extend(glob.glob(glob_path))

        keys_list = []
        for ssh_keys_path in ssh_keys_paths:
            log.info('Getting keys from {0}'.format(ssh_keys_path))
            with open(ssh_keys_path) as authorized_keys_file:
                keys_list.append(authorized_keys_file.read())

        authorized_keys_content = ''.join(keys_list)
        log.info('Save keys to {0}'.format(migration_ssh_file))
        with open(migration_ssh_file, 'w') as authorized_migration_file:
            authorized_migration_file.write(authorized_keys_content)

        system_ssh_host_keys = glob.glob(system_ssh_host_keys_glob_path)
        sshd_config_host_keys_entries = []
        log.info('Copying host ssh keys')
        for system_ssh_host_key in system_ssh_host_keys:
            if not system_ssh_host_key.endswith('ssh_host_key'):
                shutil.copy(system_ssh_host_key, '/etc/ssh/')

                if not system_ssh_host_key.endswith('.pub'):
                    live_private_ssh_host_key_path = os.sep.join(
                        [
                            os.path.dirname(sshd_config_path),
                            os.path.basename(system_ssh_host_key)
                        ]
                    )
                    entry = 'HostKey {0}'.format(
                        live_private_ssh_host_key_path
                    )
                    sshd_config_host_keys_entries.append(entry)

        with open(sshd_config_path, 'a') as live_sshd_config_file:
            # write one newline to be sure any subsequent
            # HostKey entry starts correctly
            live_sshd_config_file.write(os.linesep)
            live_sshd_config_file.write(
                os.linesep.join(sshd_config_host_keys_entries)
            )
        log.info('Restarting sshd')
        Command.run(
            ['systemctl', 'restart', 'sshd']
        )
    except Exception as issue:
        log.error(
            'SSH key/identity setup failed with: {0}. {1}'.format(
                issue, 'Continue without ssh access'
            )
        )
