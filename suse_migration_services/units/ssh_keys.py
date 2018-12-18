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
import glob

# project
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import log


def main():
    """
    DistMigration ssh access for migration user

    Copy the authoritation key found to the migration user
    directory in order to access through ssh
    """
    ssh_keys_glob_paths = Defaults.get_ssh_keys_paths()
    migration_ssh_file = Defaults.get_migration_ssh_file()
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
    except Exception:
        log.error('An error ocurred when copying ssh key files.'
                  'The migration will continue without ssh access')
        pass
