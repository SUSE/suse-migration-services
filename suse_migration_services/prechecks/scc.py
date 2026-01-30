# Copyright (c) 2025 SUSE LLC.  All rights reserved.
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
# along with suse-migration-services. If not, see <http://www.gnu.org/licenses/>#
from lxml import etree
import requests
import yaml
import logging
import os
import glob

from suse_migration_services.defaults import Defaults
from suse_migration_services.migration_target import MigrationTarget

log = logging.getLogger(Defaults.get_migration_log_name())


def migration(migration_system=False):
    """
    Send API call to ask the registration server for an upgrade path
    and report any error this request might come back with
    """
    if migration_system:
        # This check must not be called inside of the
        # migration system live iso or container image.
        # It will only be useful on the system to migrate
        # at install time of the Migration package or on
        # manual user invocation of suse-migration-pre-checks
        # prior the actual migration.
        return

    installed_products = get_installed_products()
    installed_products['target_base_product'] = MigrationTarget.get_migration_target()

    if installed_products.get('installed_products') and installed_products.get(
        'target_base_product'
    ):
        registration_server = get_registration_server_url()
        registration_credentials = get_scc_credentials()
        if registration_server and registration_credentials:
            request_migration_offer(
                installed_products, registration_credentials, registration_server
            )
            return
    log.info('System not registered, skipped')


def request_migration_offer(installed_products, registration_credentials, registration_server):
    data = {
        'installed_products': installed_products['installed_products'],
        'target_base_product': installed_products['target_base_product'],
    }
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    response = None
    try:
        uri = '{}/connect/systems/products/offline_migrations'.format(registration_server)
        user = registration_credentials['username']
        secret = registration_credentials['password']
        response = requests.post(uri, json=data, auth=(user, secret), headers=headers)
        offline_migrations = response.json()
        if isinstance(offline_migrations, dict):
            result_error = offline_migrations.get('error')
            if result_error:
                log.error(result_error)
    except Exception as issue:
        log.error(
            'Post request to {} failed with {}'.format(
                registration_server, response.text if response else issue
            )
        )


def get_scc_credentials():
    scc_credentials = '/etc/zypp/credentials.d/SCCcredentials'
    result = {}
    if os.path.isfile(scc_credentials):
        try:
            with open(scc_credentials, 'r') as config:
                for line in config.read().splitlines():
                    if line.startswith('username'):
                        result['username'] = line.split('=')[1]
                    if line.startswith('password'):
                        result['password'] = line.split('=')[1]
        except Exception as issue:
            message = 'Loading {0} failed: {1}: {2}'.format(
                scc_credentials, type(issue).__name__, issue
            )
            log.error(message)
    return result


def get_registration_server_url():
    suseconnect_config = '/etc/SUSEConnect'
    if os.path.isfile(suseconnect_config):
        try:
            with open(suseconnect_config, 'r') as config:
                scc_data = yaml.safe_load(config) or {}
                return scc_data.get('url')
        except Exception as issue:
            message = 'Loading {0} failed: {1}: {2}'.format(
                suseconnect_config, type(issue).__name__, issue
            )
            log.error(message)


def get_installed_products():
    installed_products = {'installed_products': []}
    for prod_file in glob.glob('/etc/products.d/*.prod'):
        product_tree = etree.parse(prod_file)
        installed_products['installed_products'].append(
            {
                'identifier': product_tree.find('name').text,
                'version': product_tree.find('version').text,
                'arch': product_tree.find('arch').text,
            }
        )
    return installed_products
