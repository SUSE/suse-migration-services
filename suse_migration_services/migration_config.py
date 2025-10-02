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
import yaml
import os
from textwrap import dedent
from cerberus import Validator

# project
from suse_migration_services.defaults import Defaults
from suse_migration_services.suse_product import SUSEBaseProduct
from suse_migration_services.schema import schema
from suse_migration_services.exceptions import (
    DistMigrationConfigDataException,
    DistMigrationProductNotFoundException
)

log = logging.getLogger(Defaults.get_migration_log_name())


class MigrationConfig:
    """
    **Implements reading of migration configuration file:**

    /etc/migration-config.yml

    The migration config file lives inside of the migration
    live image system. It is usually provided as a pre-setup
    version as part of the live migration image build.
    """
    def __init__(self):
        self.migration_config_file = \
            Defaults.get_migration_config_file()
        self.migration_config_dir = \
            Defaults.get_migration_config_dir()
        self.migration_custom_file = \
            Defaults.get_system_migration_custom_config_file()
        self.config_data = self._parse_config_file(
            self.migration_config_file
        )
        self._merge_configs(self._list_dropin_configs())

    def _parse_config_file(self, config_file):
        config_data = {}
        if os.path.exists(config_file):
            with open(config_file, 'r') as config:
                try:
                    validator = Validator(schema)
                    config_data = yaml.safe_load(config) or {}
                    validator.validate(config_data)
                except Exception as e:
                    message = 'Loading {0} failed: {1}: {2}'.format(
                        config_file, type(e).__name__, e
                    )
                    log.error(message)
                    raise DistMigrationConfigDataException(message)
                if validator.errors:
                    message = 'Validating {0} failed: {1}'.format(
                        config_file, validator.errors
                    )
                    log.error(message)
                    raise DistMigrationConfigDataException(message)
        return config_data

    @staticmethod
    def _merge_config_dicts(dict1, dict2):
        """
        Recursively merges dict2 into dict1.
        For keys present in both:
         * nested dictionaries are recursively called
         * lists are extended, duplicates are removed
         * all other values are overwritten.
        """
        for key, value in dict2.items():
            if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
                MigrationConfig._merge_config_dicts(dict1[key], value)
            elif key in dict1 and isinstance(dict1[key], list) and isinstance(value, list):
                dict1[key] = list(dict.fromkeys(dict1[key] + value))
            else:
                dict1[key] = value

    def _merge_configs(self, config_files):
        for f in config_files:
            data = self._parse_config_file(f)
            if data:
                MigrationConfig._merge_config_dicts(self.config_data, data)

    def _list_dropin_configs(self):
        dropin_dir = self.migration_config_dir
        dropin_files = []
        if not os.path.isdir(dropin_dir):
            return dropin_files

        for filename in os.listdir(dropin_dir):
            file_path = os.path.join(dropin_dir, filename)
            if not os.path.isfile(file_path) or not file_path.endswith('.yml'):
                continue
            dropin_files.append(file_path)

        return sorted(dropin_files)

    def get_migration_product(self):
        """
        Returns the full qualified product

        The value returned is passed to the --product option in the
        zypper migration call
        """
        # check for a custom migration product
        migration_product = self.config_data.get('migration_product')
        if not migration_product:
            migration_product = SUSEBaseProduct(log).get_product_name()
            if not migration_product:
                # auto detection went wrong
                message = (
                    'Migration product not found, aborting migration attempt.'
                )
                log.error(message)
                raise DistMigrationProductNotFoundException(message)

        return migration_product

    def get_preserve_info(self):
        """
        Return dictionary of the different list of files to be preserved.

        The returned lists, in the dictionary, are used to make those files
        available to the migration live system such that the
        same behavior the config applies on the system to be
        upgraded also applies to the live migration system
        while the upgrade runs
        """
        return self.config_data.get('preserve', False)

    def get_network_info(self):
        """
        Return dictionary of network config.
        """
        return self.config_data.get('network', False)

    def update_migration_config_file(self):
        """
        Update the default migration configuration with custom values
        """
        if os.path.exists(self.migration_custom_file):
            new_config = self._parse_config_file(self.migration_custom_file)
            if new_config:
                MigrationConfig._merge_config_dicts(self.config_data, new_config)

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

    def is_host_independent_initd_requested(self):
        return self.config_data.get('build_host_independent_initrd', False)

    def is_pre_checks_fix_requested(self):
        return self.config_data.get('pre_checks_fix', True)

    def get_migration_config_file_content(self):
        return yaml.dump(self.config_data, default_flow_style=False)

    def is_verbosity_requested(self):
        return self.config_data.get('verbose_migration', False)

    def is_zypp_solver_test_case_requested(self):
        return self.config_data.get('debug_solver', False)

    def _write_config_file(self):
        with open(self.migration_config_file, 'w') as config:
            yaml.dump(self.config_data, config, default_flow_style=False)
