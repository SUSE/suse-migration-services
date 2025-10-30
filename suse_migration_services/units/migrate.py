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
import re

# project
from suse_migration_services.command import Command
from suse_migration_services.migration_config import MigrationConfig
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger
from suse_migration_services.zypper import Zypper
from suse_migration_services.units.post_mount_system import (
    update_env, log_env
)

from suse_migration_services.exceptions import (
    DistMigrationZypperException,
)


def duplicate_solver_test_case_data():
    """
    We duplicate the created solver test case to cover both use cases
    a user looging into the migration system and wanting to see the
    solver case and a user expecting the solver case to be on the
    system that is/has being migrated.
    """
    test_case_dir = Defaults.get_zypper_solver_test_case_dir()

    if os.path.isdir(test_case_dir):
        target = os.sep.join(
            [Defaults.get_system_root_path(), test_case_dir]
        )
        Command.run(
            ['cp', '-r', test_case_dir, target]
        )


def is_single_rpmtrans_requested() -> str:
    """
    Return the value of single_rpmtrans

    The value is read from the kernel command line argument:
    migration.single_rpmtrans=<value>
    """
    # The default is 0
    single_rpmtrans = '0'
    with open('/proc/cmdline', 'r') as f:
        cmdline = f.read()
    match = re.search(r'migration.single_rpmtrans=([\w]+)', cmdline)
    if match:
        value = match.group(1).lower()
        if value == 'true' or value == '1':
            single_rpmtrans = '1'
    return single_rpmtrans


def main():
    """
    DistMigration run zypper based migration

    Call zypper migration plugin and migrate the system.
    The output of the call is logged on the system to migrate
    """
    Logger.setup()
    log = logging.getLogger(Defaults.get_migration_log_name())
    root_path = Defaults.get_system_root_path()
    exit_code_file = Defaults.get_migration_exit_code_file()

    try:
        log.info('Running migrate service')
        migration_config = MigrationConfig()
        migration_config.update_migration_config_file()
        log.info(
            'Config file content:\n{content}\n'. format(
                content=migration_config.get_migration_config_file_content()
            )
        )
        if migration_config.get_preserve_info():
            # set potential missing settings in env
            log.info('Update env variables')
            update_env(migration_config.get_preserve_info())
            log_env(log)
        verbose_migration = '--no-verbose'
        if migration_config.is_verbosity_requested():
            verbose_migration = '--verbose'
        solver_case = Defaults.get_zypp_gen_solver_test_case()
        if migration_config.is_zypp_solver_test_case_requested():
            solver_case = '--debug-solver'
        os.environ['ZYPP_SINGLE_RPMTRANS'] = is_single_rpmtrans_requested()
        os.environ['ZYPP_NO_USRMERGE_PROTECT'] = is_single_rpmtrans_requested()

        if migration_config.is_zypper_migration_plugin_requested():
            Zypper.run(
                [
                    'migration',
                    verbose_migration,
                    solver_case,
                    '--non-interactive',
                    '--gpg-auto-import-keys',
                    '--no-selfupdate',
                    '--auto-agree-with-licenses',
                    '--allow-vendor-change',
                    '--strict-errors-dist-migration',
                    '--replacefiles',
                    '--product', migration_config.get_migration_product(),
                    '--root', root_path
                ]
            )
        else:
            zypper_call = Zypper.run(
                [
                    '--no-cd',
                    '--non-interactive',
                    '--gpg-auto-import-keys',
                    '--root', root_path,
                    'dup',
                    '--auto-agree-with-licenses',
                    '--allow-vendor-change',
                    '--download', 'in-advance',
                    '--replacefiles',
                    '--allow-downgrade'
                ],
                raise_on_error=False)
            zypper_call.raise_if_failed()
        # report success(0) return code
        with open(exit_code_file, 'w') as exit_code:
            exit_code.write('0{}'.format(os.linesep))
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
        # report failed(1) return code
        with open(exit_code_file, 'w') as exit_code:
            exit_code.write('1{}'.format(os.linesep))
        log.error('migrate service failed with {0}'.format(issue))
        raise DistMigrationZypperException(
            'Migration failed with {0}'.format(issue)
        )
    finally:
        duplicate_solver_test_case_data()
