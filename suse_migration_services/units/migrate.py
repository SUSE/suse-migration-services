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
import os

# project
from suse_migration_services.migration_config import MigrationConfig
from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger

from suse_migration_services.exceptions import (
    DistMigrationZypperException,
    DistMigrationCommandException
)


def main():
    """
    DistMigration run zypper based migration

    Call zypper migration plugin and migrate the system.
    The output of the call is logged on the system to migrate
    """
    Logger.setup()
    log = logging.getLogger(Defaults.get_migration_log_name())
    root_path = Defaults.get_system_root_path()

    try:
        log.info('Running migrate service')
        migration_config = MigrationConfig()
        if migration_config.is_zypper_migration_plugin_requested():
            bash_command = ' '.join(
                [
                    'zypper', 'migration',
                    '--non-interactive',
                    '--gpg-auto-import-keys',
                    '--no-selfupdate',
                    '--auto-agree-with-licenses',
                    '--allow-vendor-change',
                    '--strict-errors-dist-migration',
                    '--replacefiles',
                    '--product', migration_config.get_migration_product(),
                    '--root', root_path,
                    '&>>', Defaults.get_migration_log_file()
                ]
            )
            Command.run(
                ['bash', '-c', bash_command]
            )
        else:
            bash_command = ' '.join(
                [
                    'zypper',
                    '--no-cd',
                    '--non-interactive',
                    '--gpg-auto-import-keys',
                    '--root', root_path,
                    'dup',
                    '--auto-agree-with-licenses',
                    '--allow-vendor-change',
                    '--download', 'in-advance',
                    '--replacefiles',
                    '--allow-downgrade',
                    '&>>', Defaults.get_migration_log_file()
                ]
            )
            zypper_call = Command.run(
                ['bash', '-c', bash_command], raise_on_error=False
            )
            if zypper_has_failed(zypper_call.returncode):
                raise DistMigrationCommandException(
                    '{0} failed with: {1}: {2}'.format(
                        bash_command, zypper_call.output, zypper_call.error
                    )
                )
    except Exception as issue:
        etc_issue_path = os.sep.join(
            [root_path, 'etc/issue']
        )
        log_path_migrated_system = os.sep + os.path.relpath(
            Defaults.get_migration_log_file(), root_path
        )
        with open(etc_issue_path, 'w') as issue_file:
            issue_file.write(
                'Migration has failed, for further details see {0}'.format(
                    log_path_migrated_system
                )
            )
        log.error('migrate service failed with {0}'.format(issue))
        raise DistMigrationZypperException(
            'Migration failed with {0}'.format(issue)
        )


def zypper_has_failed(returncode):
    """
    Evaluate given result return code

    In zypper any return code == 0 or >= 100 is considered success.
    Any return code different from 0 and < 100 is treated as an
    error we care for. Return codes >= 100 indicates an issue
    like 'new kernel needs reboot of the system' or similar which
    we don't care in the scope of image building

    :param int returncode: return code number

    :return: True|False

    :rtype: boolean
    """
    error_codes = [
        104,  # ZYPPER_EXIT_INF_CAP_NOT_FOUND
        105,  # ZYPPER_EXIT_ON_SIGNAL
        106,  # ZYPPER_EXIT_INF_REPOS_SKIPPED
    ]

    if returncode == 0:
        # All is good
        return False
    elif returncode in error_codes:
        return True
    elif returncode >= 100:
        # Treat all other 100 codes as non error codes
        return False

    # Treat any other error code as error
    return True
