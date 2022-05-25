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
"""systemd service to run pre_checks"""
import logging

# project
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger
from suse_migration_services.migration_config import MigrationConfig
from suse_migration_services.prechecks.pre_checks import \
    check_repos, check_fs, check_multi_kernels


def main():
    """DistMigration run the pre_checks before the system is started"""

    Logger.setup()
    log = logging.getLogger(Defaults.get_migration_log_name())

    log.info("Running suse-migration-pre-checks")
    if MigrationConfig().is_pre_checks_fix_requested():
        log.info("Using the '--fix' option")

    check_repos.remote_repos()
    check_fs.encryption()
    check_multi_kernels.multiversion_and_multiple_kernels(True, True)
