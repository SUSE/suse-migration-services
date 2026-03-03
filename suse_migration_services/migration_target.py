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
import platform
from glob import glob
from fnmatch import fnmatch
from textwrap import dedent

from suse_migration_services.migration_config import MigrationConfig
from suse_migration_services.defaults import Defaults

log = logging.getLogger(Defaults.get_migration_log_name())


class MigrationTarget:
    """
    Implements the detection of migration target
    """

    @staticmethod
    def get_migration_target():
        migration_config = MigrationConfig()
        migration_product = migration_config.config_data.get('migration_product')
        if migration_product:
            product = migration_product.split('/')
            return {'identifier': product[0], 'version': product[1], 'arch': product[2]}
        migration_iso = glob('/migration-image/*-*Migration.*.iso')
        migration_iso = migration_iso[0] if migration_iso else ''

        if fnmatch(migration_iso, '*SLES15-SAP*Migration*.iso'):
            return {'identifier': 'SLES_SAP', 'version': '15.4', 'arch': platform.machine()}
        elif fnmatch(migration_iso, '*SLES16-SAP*Migration*.iso'):
            return {'identifier': 'SLES_SAP', 'version': '16.0', 'arch': platform.machine()}
        elif fnmatch(migration_iso, '*SLES16*-*Migration*.iso'):
            return {'identifier': 'SLES', 'version': '16.0', 'arch': platform.machine()}
        else:
            message = dedent(
                '''\n
                Migration target cannot be detected, fallback to SLES 15.7

                Please make sure to install one of the following Migration packages

                - SLES15-Migration
                - SLES15-SAP-Migration
                - SLES16-Migration
                - SLES16-SAP-Migration

                Only with an installed Migration package, the DMS knows which migration
                target to use and can ask the registration server for an upgrade path.
                The following request to the registration server might provide incorrect
                information due to an assumption of the migration target:
            '''
            )
            log.warning(message)
            return {'identifier': 'SLES', 'version': '15.7', 'arch': platform.machine()}
