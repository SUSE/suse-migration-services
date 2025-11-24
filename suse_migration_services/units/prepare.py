# Copyright (c) 2018 SUSE Linux LLC.  All rights reserved.
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
import glob
import logging
import os
import shutil
from configparser import ConfigParser

# project
from suse_migration_services.migration_config import MigrationConfig
from suse_migration_services.path import Path
from suse_migration_services.command import Command
from suse_migration_services.fstab import Fstab
from suse_migration_services.defaults import Defaults
from suse_migration_services.suse_connect import SUSEConnect
from suse_migration_services.logger import Logger
from suse_migration_services.units.setup_host_network import SetupHostNetwork

from suse_migration_services.exceptions import (
    DistMigrationZypperMetaDataException,
    DistMigrationSystemNotRegisteredException,
)


class PrepareMigration:
    def __init__(self):
        """
        DistMigration prepare for migration

        Prepare the migration live system to allow zypper migration to
        upgrade the system across major distribution versions. The zypper
        migration process contacts the service that provides the configured
        repositories on the system being migrated. The service must be one
        of SUSE's repository services, SCC, RMT, or SMT. This requiers
        information from the target system. This service makes the necessary
        information available inside the live system that performs the
        migration.
        """
        Logger.setup()
        self.log = logging.getLogger(Defaults.get_migration_log_name())
        self.root_path = Defaults.get_system_root_path()
        self.suse_connect_setup = os.sep.join(
            [self.root_path, 'etc', 'SUSEConnect']
        )
        self.suse_cloud_regionsrv_setup = os.sep.join(
            [self.root_path, 'etc', 'regionserverclnt.cfg']
        )
        self.hosts_setup = os.sep.join(
            [self.root_path, 'etc', 'hosts']
        )
        self.migration_suse_cloud_regionsrv_setup = '/etc/regionserverclnt.cfg'
        self.trust_anchors = [
            '/usr/share/pki/trust/anchors/',
            '/etc/pki/trust/anchors/'
        ]
        self.cache_cloudregister_path = '/var/cache/cloudregister'
        self.cloud_register_certs_path_fallback = '/usr/lib/regionService/certs'
        self.cloud_register_certs_bind_mount_path = ''
        self.cloud_register_metadata_path = ''
        self.cloud_register_certs_path = ''

    def perform(self):
        self.log.info('Running prepare for migration')
        if os.path.exists(self.suse_connect_setup):
            shutil.copy(
                self.suse_connect_setup, '/etc/SUSEConnect'
            )
        if os.path.exists(self.suse_cloud_regionsrv_setup):
            shutil.copy(
                self.suse_cloud_regionsrv_setup,
                self.migration_suse_cloud_regionsrv_setup
            )
            self.update_regionsrv_setup()
            self.cloud_register_certs_path = self.get_regionsrv_certs_path(
                self.cloud_register_certs_path_fallback
            )
            self.cloud_register_certs_bind_mount_path = \
                os.path.normpath(
                    os.sep.join(
                        [self.root_path, self.cloud_register_certs_path]
                    )
                )
            self.report_if_regionsrv_certs_not_found(
                os.path.normpath(
                    os.sep.join(
                        [self.root_path, self.cloud_register_certs_path]
                    )
                )
            )
        if os.path.exists(self.hosts_setup):
            shutil.copy(
                self.hosts_setup, '/etc/hosts'
            )
        for trust_anchor in self.trust_anchors:
            root_trust_anchor = os.path.normpath(
                os.sep.join([self.root_path, trust_anchor])
            )
            if os.path.isdir(root_trust_anchor):
                certificates = os.listdir(root_trust_anchor)
                if certificates:
                    Path.create(trust_anchor)
                    for cert in certificates:
                        cert_file = os.sep.join([root_trust_anchor, cert])
                        if os.path.islink(cert_file):
                            cert_file = os.sep.join(
                                [self.root_path, os.readlink(cert_file)]
                            )
                        self.log.info('Importing certificate: %s', cert_file)
                        try:
                            shutil.copy(cert_file, trust_anchor)
                        except FileNotFoundError as issue:
                            self.log.warning(
                                'Import of {} failed with {}'.format(
                                    cert_file, issue
                                )
                            )
                    self.log.info('Update certificate pool')
                    Command.run(
                        ['update-ca-certificates']
                    )

        zypp_metadata = os.sep.join(
            [self.root_path, 'etc', 'zypp']
        )
        zypp_plugins_services = os.sep.join(
            [self.root_path, 'usr', 'lib', 'zypp', 'plugins', 'services']
        )

        with open(self.hosts_setup, 'r', encoding="utf-8") as fp:
            contents = fp.read()
            self.log.info(
                'Dumping Hosts file:{}{}'.format(os.linesep, contents)
            )
            if 'susecloud.net' in contents:
                self.log.info(
                    'Found an entry for "susecloud.net" in {}'.format(
                        self.hosts_setup
                    )
                )
                try:
                    self.cloud_register_metadata_path = \
                        self.get_regionsrv_client_file_location()
                except DistMigrationZypperMetaDataException as issue:
                    message = 'Failed locating regionsrv-client cache files: {}'
                    self.log.error(message.format(issue))
                    raise

        zypper_log_file = os.sep.join(
            [self.root_path, 'var', 'log', 'zypper.log']
        )
        if os.path.exists(zypper_log_file):
            try:
                zypper_host_log_file = zypper_log_file.replace(
                    self.root_path, ''
                )
                if not os.path.exists(zypper_host_log_file):
                    with open(zypper_host_log_file, 'w'):
                        # we bind mount the system zypper log file
                        # but the mount target does not exist.
                        # Create it as empty file prior bind mounting
                        pass
                    Command.run(
                        [
                            'mount', '--bind',
                            zypper_log_file, zypper_host_log_file
                        ]
                    )
            except Exception as issue:
                self.log.warning(
                    'Bind mounting zypper log file failed with: {0}'.format(
                        issue
                    )
                )
        try:
            # log network info as network-online.target is done at this point
            SetupHostNetwork().log_network_details()
            system_mount = Fstab()
            system_mount.read(
                Defaults.get_system_mount_info_file()
            )
            self.log.info('Bind mounting /etc/zypp')
            Command.run(
                ['mount', '--bind', zypp_metadata, '/etc/zypp']
            )
            system_mount.add_entry(
                zypp_metadata, '/etc/zypp'
            )
            self.log.info('Bind mounting /usr/lib/zypp/plugins')
            Command.run(
                [
                    'mount', '--bind', zypp_plugins_services,
                    '/usr/lib/zypp/plugins/services'
                ]
            )
            system_mount.add_entry(
                zypp_plugins_services, '/usr/lib/zypp/plugins/services'
            )
            if os.path.exists(self.cloud_register_metadata_path):
                self.log.info(
                    'Bind mounting {0} from {1}'.format(
                        self.cache_cloudregister_path,
                        self.cloud_register_metadata_path
                    )
                )
                Path.create(self.cache_cloudregister_path)
                Command.run(
                    [
                        'mount', '--bind',
                        self.cloud_register_metadata_path,
                        self.cache_cloudregister_path
                    ]
                )
            if os.path.exists(self.cloud_register_certs_bind_mount_path):
                self.log.info(
                    'Bind mounting {0} from {1}'.format(
                        self.cloud_register_certs_path,
                        self.cloud_register_certs_bind_mount_path
                    )
                )
                Path.create(self.cloud_register_certs_path)
                Command.run(
                    [
                        'mount', '--bind',
                        self.cloud_register_certs_bind_mount_path,
                        self.cloud_register_certs_path
                    ]
                )
                self.report_if_regionsrv_certs_not_found(
                    self.cloud_register_certs_path
                )
                update_smt_cache = '/usr/sbin/updatesmtcache'
                if os.path.isfile(update_smt_cache):
                    self.log.info('Updating SMT cache')
                    Command.run(
                        [update_smt_cache]
                    )
            system_mount.export(
                Defaults.get_system_mount_info_file()
            )
            # Check if system is registered
            migration_config = MigrationConfig()
            migration_config.update_migration_config_file()
            self.log.info(
                'Config file content:\n{content}\n'. format(
                    content=migration_config.get_migration_config_file_content()
                )
            )
            if migration_config.is_zypper_migration_plugin_requested():
                if not SUSEConnect.is_registered(self.log):
                    message = 'System not registered. Aborting migration.'
                    self.log.error(message)
                    raise DistMigrationSystemNotRegisteredException(
                        message
                    )
        except Exception as issue:
            self.log.error(
                'Preparation of zypper metadata failed with {0}'.format(
                    issue
                )
            )
            # Not unmounting any of the bind mounts above; the reboot
            # service should take care of that anyway
            raise DistMigrationZypperMetaDataException(
                'Preparation of zypper metadata failed with {0}'.format(
                    issue
                )
            )

    def get_regionsrv_certs_path(self, fallback):
        """
        Note: This method is specific to the SUSE Public Cloud Infrastructure

        Retrieve the certlocation from the specified suse_cloud_regionsrv_setup
        config's server.certlocation setting, defaulting to fallback value
        if not found.
        """
        regionsrv_setup = ConfigParser()
        regionsrv_setup.read(self.suse_cloud_regionsrv_setup)
        return regionsrv_setup.get(
            'server', 'certlocation', fallback=fallback
        )

    def report_if_regionsrv_certs_not_found(self, certs_path):
        """
        Log a message if no PEM files are found at the specified certs path
        in the system being migrated.
        """
        if not glob.glob(os.path.join(certs_path, '*.pem')):
            self.log.info(
                'No certs found under specified certs path: {}'.format(
                    certs_path
                )
            )

    def update_regionsrv_setup(self):
        """
        Note: This method is specific to the SUSE Public Cloud Infrastructure

        Update regionserverclnt.cfg config file when running in the Azure
        Cloud. The method modifies the pre-configured azuremetadata call
        in a way that it passes the root device as option to skip the
        automated detection of that device. The implementation in azuremetadata
        does not work when used inside of the special migration live system.
        """
        regionsrv_setup = ConfigParser()
        regionsrv_setup.read(self.suse_cloud_regionsrv_setup)
        dataProvider = regionsrv_setup.get('instance', 'dataProvider')
        if 'azuremetadata' in dataProvider:
            root_disk_device = self.get_root_disk_device()
            if root_disk_device:
                dataProvider += ' --device {0}'.format(root_disk_device)
                regionsrv_setup.set('instance', 'dataProvider', dataProvider)
                with open(self.suse_cloud_regionsrv_setup, 'w') as regionsrv_fd:
                    regionsrv_setup.write(regionsrv_fd)

    def get_root_disk_device(self):
        """
        Find unix disk device which is associated with the
        root mount point given in root_path
        """
        root_device = Command.run(
            [
                'findmnt', '--first', '--noheadings',
                '--output', 'SOURCE', '--mountpoint', self.root_path
            ]
        ).output
        if root_device:
            # The findmnt output can contain extra volume information
            # which we don't need for the subsequent lsblk call.
            root_device = root_device.split('[')[0]
            lsblk_call = Command.run(
                [
                    'lsblk', '-p', '-n', '-r', '-s', '-o',
                    'NAME,TYPE', root_device.strip()
                ]
            )
            considered_block_types = ['disk', 'raid']
            for entry in lsblk_call.output.split(os.linesep):
                block_record = entry.split()
                if len(block_record) >= 2:
                    block_type = block_record[1]
                    if block_type in considered_block_types:
                        return block_record[0]

    def get_regionsrv_client_file_location(self):
        """
        Find the correct path for the cloud-regionsrv-client cache files
        as the location moves from /var/lib/cloudregister
        (pre cloud-regionsrv-client-10.0.4) to /var/cache/cloudregister
        (post cloud-regionsrv-client-10.0.4)
        """
        for cloud_register_path in [
            os.sep.join([self.root_path, 'var', 'cache', 'cloudregister']),
            os.sep.join([self.root_path, 'var', 'lib', 'cloudregister'])
        ]:
            self.log.info(
                'Looking for cache files in: {}'.format(cloud_register_path)
            )
            if os.path.isdir(cloud_register_path) and \
                    any('SMT' in x for x in os.listdir(cloud_register_path)):
                self.log.info(
                    'Cache dir exists and contains: {}'.format(
                        os.listdir(cloud_register_path)
                    )
                )
                return cloud_register_path
        raise DistMigrationZypperMetaDataException(
            'No cloud-regionsrv-client cache files found in '
            '/var/cache/cloudregister or /var/lib/cloudregister'
        )


def main():
    prepare_system = PrepareMigration()
    prepare_system.perform()
