# Copyright (c) 2019 SUSE Linux LLC.  All rights reserved.
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

# project
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger
from suse_migration_services.suse_product import SUSEBaseProduct

from suse_migration_services.exceptions import (
    DistMigrationProductSetupException
)


def main():
    """
    DistMigration setup baseproduct for migration

    Creates a backup of the system products data and prepares
    the baseproduct to be suitable for the distribution migration.
    In case of an error the backup information is used by the
    zypper migration plugin to restore the original product
    data such that the plugin's rollback mechanism is not
    negatively influenced.
    """
    Logger.setup()
    log = logging.getLogger(Defaults.get_migration_log_name())
    log.info('Running setup baseproduct for migration')
    try:
        # Note:
        # zypper implements a handling for the distro_target attribute.
        # If present in the repository metadata, zypper compares the
        # value with the baseproduct <target> setup in /etc/products.d.
        # If they mismatch zypper refuses to create the repo. In the
        # process of a migration from distribution [A] to [B] this mismatch
        # always applies by design and prevents the zypper migration
        # plugin to work. In SCC or RMT the repositories doesn't
        # contain the distro_target attribute which is the reason
        # why we don't see this problem there. SMT however creates repos
        # including distro_target. The current workaround solution is
        # to delete the target specification in the baseproduct
        # registration if present.
        log.info('Updating Base Product to be suitable for migration')
        SUSEBaseProduct(log).delete_target_registration()
    except Exception as issue:
        message = 'Base Product update failed with: {0}'.format(issue)
        log.error(message)
        raise DistMigrationProductSetupException(message)
