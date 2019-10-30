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
import os
import glob
from xml.etree.ElementTree import ElementTree

# project
from suse_migration_services.defaults import Defaults
from suse_migration_services.command import Command
from suse_migration_services.logger import log
from suse_migration_services.exceptions import (
    DistMigrationSUSEBaseProductException
)


class SUSEBaseProduct(object):
    def __init__(self):
        root_path = Defaults.get_system_root_path()
        self.products_metadata = os.sep.join(
            [root_path, 'etc', 'products.d']
        )
        self.prod_filenames = glob.glob(
            os.path.join(self.products_metadata, '*.prod')
        )
        base_product_files = []
        xml = ElementTree()
        for prod_filename in self.prod_filenames:
            print(prod_filename)
            try:
                xml.parse(prod_filename)
                register_sections = xml.findall('register')
                for register in register_sections:
                    flavor = register.findall('flavor')
                    if not flavor:
                        base_product_files.append(prod_filename)

            except Exception as issue:
                message = \
                    'Parsing XML file {0} failed with: {1}'.format(
                        prod_filename, issue
                    )
                log.warning(message)

        if len(base_product_files) != 1:
            if not base_product_files:
                message = 'There is no baseproduct'
            else:
                message = (
                    'Found multiple product definitions '
                    'without element <flavor>: \n{0}'
                    .format('\n'.join(base_product_files))
                )
            log.error(message)
            raise DistMigrationSUSEBaseProductException(message)

        self.base_product = base_product_files[0]

    def delete_target_registration(self):
        self.backup_products_metadata()
        xml = ElementTree()
        try:
            xml.parse(self.base_product)
            register_sections = xml.findall('register')
            for register in register_sections:
                target_sections = register.findall('target')
                for target in target_sections:
                    register.remove(target)
            xml.write(
                self.base_product, encoding="UTF-8", xml_declaration=True
            )
        except Exception as issue:
            log.error(
                'Could not delete target registration with {0}'.format(issue)
            )

    def backup_products_metadata(self):
        """
        Back up the products information.

        In case migration fails and the migration rolls back to the
        previous state. The rollback restores this info back in place.
        """
        log.info('Creating backup of Product data')
        Command.run(
            [
                'rsync', '-zav', '--delete', self.products_metadata + os.sep,
                '/tmp/products.d.backup/'
            ]
        )

    def get_tag(self, tag):
        """Get the content of tag if any."""
        xml = ElementTree()
        try:
            xml.parse(self.base_product)
            tag_nodes = xml.findall(tag)
            return [tag_node.text for tag_node in tag_nodes]
        except Exception as issue:
            # if we are here, it means no potentially no migration
            # product is defined
            log.warning(
                'Parsing XML file {0} failed with: {1}'
                .format(self.base_product, issue)
            )

    def get_product_name(self):
        """Get the product name to be migrated to."""
        migration_product_name = None
        try:
            name = self.get_tag('name')[0]
            arch = self.get_tag('arch')[0]
            if name and arch:
                migration_product_name = '/'.join(
                    [name, self.get_default_target_version(), arch]
                )
        except Exception as issue:
            log.error(
                'Base product could not be detected: {0}.'.format(issue)
            )

        return migration_product_name

    def get_default_target_version(self):
        return Defaults.get_os_release().version_id
