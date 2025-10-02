
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
import yaml
import os
import platform
from glob import glob
from fnmatch import fnmatch

from suse_migration_services.defaults import Defaults

log = logging.getLogger(Defaults.get_migration_log_name())


class MigrationTarget:
    """Implements the detection of migration target"""
    @staticmethod
    def _parse_custom_config():
        migration_config = '/etc/sle-migration-service.yml'
        if os.path.isfile(migration_config):
            try:
                with open(migration_config, 'r') as config:
                    return yaml.safe_load(config) or {}
            except Exception as issue:
                message = 'Loading {0} failed: {1}: {2}'.format(
                    migration_config, type(issue).__name__, issue
                )
                log.error(message)

        return {}

    @staticmethod
    def get_migration_target():
        config_data = MigrationTarget._parse_custom_config()
        migration_product = config_data.get('migration_product')
        if migration_product:
            product = migration_product.split('/')
            return {
                'identifier': product[0],
                'version': product[1],
                'arch': product[2]
            }
        migration_iso = glob('/migration-image/*-*Migration.*.iso')
        if not migration_iso:
            return {}
        migration_iso = migration_iso[0]

        if fnmatch(migration_iso, '*SLES16*-*Migration*.iso'):
            # return default migration target
            return {
                'identifier': 'SLES',
                'version': '16.0',
                'arch': platform.machine()
            }
        else:
            # return default migration target
            return {
                'identifier': 'SLES',
                'version': '15.4',
                'arch': platform.machine()
            }
