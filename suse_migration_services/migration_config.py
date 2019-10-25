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
import os
from textwrap import dedent

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
        self.config_data = {}
        self.migration_config_file = \
            Defaults.get_migration_config_file()
        self.migration_custom_file = \
            Defaults.get_system_migration_custom_config_file()
        with open(self.migration_config_file, 'r') as config:
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

    def get_preserve_udev_rules_list(self):
        """
        Returns list of udev rule file(s)

        The returned file list is used to make those rule files
        available to the migration live system such that the
        same behavior the rules apply on the system to be
        upgraded also applies to the live migration system
        while the upgrade runs
        """
        preserve_data = self.config_data.get('preserve')
        if preserve_data:
            return preserve_data.get('rules')

    def update_migration_config_file(self):
        """
        Update the default migration configuration with custom values
        """
        if os.path.exists(self.migration_custom_file):
            with open(self.migration_custom_file, 'r') as custom_config:
                new_config = yaml.safe_load(custom_config)
                self.config_data.update(new_config)

            self._write_config_file()

            message = dedent('''
                The migration file '{0}' has been updated with '{1}' info
            ''')
            log.info(
                message.format(
                    self.migration_config_file, self.migration_custom_file
                ).lstrip()
            )

    def is_debug_requested(self):
        return self.config_data.get('debug', False)

    def is_zypper_migration_plugin_requested(self):
        return self.config_data.get('use_zypper_migration', True)

    def is_soft_reboot_requested(self):
        return self.config_data.get('soft_reboot', True)

    def _write_config_file(self):
        with open(self.migration_config_file, 'w') as config:
            yaml.dump(self.config_data, config, default_flow_style=False)
