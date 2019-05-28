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
import yaml

# project
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import log
from suse_migration_services.exceptions import (
    DistMigrationProductNotFoundException
)


class MigrationConfig(object):
    """
    **Implements reading of migration configuration file:**

    /etc/migration-config.yml

    The migration config file lives inside of the migration
    live image system. It is usually provided as a pre-setup
    version as part of the live migration image build.
    """
    def __init__(self):
        self.config_data = None
        with open(Defaults.get_migration_config_file(), 'r') as config:
            self.config_data = yaml.safe_load(config)

    def get_migration_product(self):
        """
        Returns the full qualified product

        The value returned is passed to the --product option in the
        zypper migration call
        """
        migration_product = self.config_data.get('migration_product')
        if not migration_product:
            message = (
                'Migration product not found, aborting migration attempt.'
            )
            log.error(message)
            raise DistMigrationProductNotFoundException(message)

        return migration_product

    def is_debug_requested(self):
        return self.config_data.get('debug', False)
