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
from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import log

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
    root_path = Defaults.get_system_root_path()

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
        products_metadata = os.sep.join(
            [root_path, 'etc', 'products.d']
        )
        if os.path.exists(products_metadata):
            log.info('Creating backup of Product data')
            Command.run(
                [
                    'rsync', '-zav', '--delete', products_metadata + os.sep,
                    '/tmp/products.d.backup/'
                ]
            )
        baseproducts = get_baseproduct(products_metadata)
        if len(baseproducts) != 1:
            if not baseproducts:
                message = 'There is no baseproduct'
            else:
                message = ('Found multiple product definitions '
                           'without element <flavor>: \n{0}'
                           .format('\n'.join(baseproducts)))
            log.error(message)
            raise DistMigrationProductSetupException(message)

        log.info('Updating Base Product to be suitable for migration')
        delete_target_registration(baseproducts[0])
    except Exception as issue:
        message = 'Base Product update failed with: {0}'.format(issue)
        log.error(message)
        raise DistMigrationProductSetupException(message)


def get_baseproduct(products_metadata):
    prod_filenames = glob.glob(
        os.path.join(products_metadata, '*.prod')
    )
    base_product_files = []
    xml = ElementTree()
    for prod_filename in prod_filenames:
        try:
            xml.parse(prod_filename)
            register_sections = xml.findall('register')
            for register in register_sections:
                flavor = register.findall('flavor')
                if not flavor:
                    base_product_files.append(prod_filename)

        except Exception as issue:
            log.warning(
                'Parsing XML file {0} failed with: {1}'
                .format(prod_filename, issue)
            )

    return base_product_files


def delete_target_registration(baseproduct_prod_filename):
    try:
        xml = ElementTree()
        xml.parse(baseproduct_prod_filename)
        register_sections = xml.findall('register')
        for register in register_sections:
            target_sections = register.findall('target')
            for target in target_sections:
                register.remove(target)
        xml.write(
            baseproduct_prod_filename, encoding="UTF-8", xml_declaration=True
        )
    except Exception as issue:
        log.error(
            'Could not delete target registration with {0}'.format(issue)
        )
