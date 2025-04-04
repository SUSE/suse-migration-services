# Copyright (c) 2022 SUSE Linux LLC.  All rights reserved.
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
"""Run various pre-checks"""
import argparse
import logging
import os

from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger
from suse_migration_services.migration_config import MigrationConfig

import suse_migration_services.prechecks.repos as check_repos
import suse_migration_services.prechecks.fs as check_fs
import suse_migration_services.prechecks.kernels as check_multi_kernels
import suse_migration_services.prechecks.ltss as ltss


def main():
    """
    DistMigration pre checks before migration starts

    Checks whether
      - repositories' locations are not remote
      - filesystems in fstab are using LUKS encryption
      - Multiple kernels are installed on the system and multiversion.kernels
        in /etc/zypp/zypp.conf is not set to 'running, latest'
    """

    Logger.setup()
    log = logging.getLogger(Defaults.get_migration_log_name())

    cli_parser = argparse.ArgumentParser(
        prog='suse-migration-pre-checks',
        description='Check for existing conditions that will cause a migration to fail'
    )

    cli_parser.add_argument(
        '-f',
        '--fix',
        action='store_true',
        help="Perform fixes to remediate potential issues that may cause "
             "the migration to fail. For example, remove extra superseeded "
             "kernels and set 'multiversion.kernels = running,latest'. "
             "Additional details can be found in the Distribution Migration "
             "System documentation."
    )

    args = cli_parser.parse_args()
    log.info('Running suse-migration-pre-checks '
             'with options: fix: %s',
             args.fix)
    migration_system_mode = False
    dms_env_var = os.environ.get('SUSE_MIGRATION_PRE_CHECKS_MODE', None)

    if dms_env_var == 'migration_system_iso_image':
        log.info("Using migration_system mode")
        migration_system_mode = True

    if args.fix and migration_system_mode and not MigrationConfig().is_pre_checks_fix_requested():
        log.info("The distribution migration system configuration value "
                 "'pre_checks_fix' is set to 'False'. Overriding the 'fix' "
                 "option and not applying pre-check fixes during the "
                 "migration.")
        args.fix = False

    check_repos.remote_repos(migration_system=migration_system_mode)
    check_fs.encryption(migration_system=migration_system_mode)
    check_multi_kernels.multiversion_and_multiple_kernels(
        fix=args.fix, migration_system=migration_system_mode
    )
    ltss.check_enabled(
        migration_system=migration_system_mode
    )
