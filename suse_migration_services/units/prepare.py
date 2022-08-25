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
from suse_migration_services.units.setup_host_network import (
    log_network_details
)

from suse_migration_services.exceptions import (
    DistMigrationZypperMetaDataException,
    DistMigrationSystemNotRegisteredException,
)


def main():
    """
    DistMigration prepare for migration

    Prepare the migration live system to allow zypper migration to
    upgrade the system across major distribution versions. The zypper
    migration process contacts the service that provides the configured
    repositories on the system being migrated. The service must be one
    of SUSE's repository services, SCC, RMT, or SMT. This requiers
    information from the target system. This service makes the necessary
    information available inside the live system that performs the migration.
    """
    Logger.setup()
    log = logging.getLogger(Defaults.get_migration_log_name())
    root_path = Defaults.get_system_root_path()
    suse_connect_setup = os.sep.join(
        [root_path, 'etc', 'SUSEConnect']
    )
    suse_cloud_regionsrv_setup = os.sep.join(
        [root_path, 'etc', 'regionserverclnt.cfg']
    )
    hosts_setup = os.sep.join(
        [root_path, 'etc', 'hosts']
    )
    trust_anchors = [
        '/usr/share/pki/trust/anchors/',
        '/etc/pki/trust/anchors/'
    ]
    cache_cloudregister_path = '/var/cache/cloudregister'
    cloud_register_metadata = ""

    if os.path.exists(suse_connect_setup):
        shutil.copy(
            suse_connect_setup, '/etc/SUSEConnect'
        )
    if os.path.exists(suse_cloud_regionsrv_setup):
        migration_suse_cloud_regionsrv_setup = '/etc/regionserverclnt.cfg'
        shutil.copy(
            suse_cloud_regionsrv_setup, migration_suse_cloud_regionsrv_setup
        )
        update_regionsrv_setup(
            root_path, migration_suse_cloud_regionsrv_setup
        )
    if os.path.exists(hosts_setup):
        shutil.copy(
            hosts_setup, '/etc/hosts'
        )
    for trust_anchor in trust_anchors:
        root_trust_anchor = os.path.normpath(
            os.sep.join([root_path, trust_anchor])
        )
        if os.path.isdir(root_trust_anchor):
            certificates = os.listdir(root_trust_anchor)
            if certificates:
                Path.create(trust_anchor)
                for cert in certificates:
                    cert_file = os.sep.join([root_trust_anchor, cert])
                    if os.path.islink(cert_file):
                        cert_file = os.sep.join(
                            [root_path, os.readlink(cert_file)]
                        )
                    log.info('Importing certificate: %s', cert_file)
                    try:
                        shutil.copy(cert_file, trust_anchor)
                    except FileNotFoundError as issue:
                        log.warning(
                            'Import of %s failed with %s', repr(cert_file),
                            repr(issue)
                        )
                log.info('Update certificate pool')
                Command.run(
                    ['update-ca-certificates']
                )

    zypp_metadata = os.sep.join(
        [root_path, 'etc', 'zypp']
    )
    zypp_plugins_services = os.sep.join(
        [root_path, 'usr', 'lib', 'zypp', 'plugins', 'services']
    )

    with open(hosts_setup, 'r', encoding="utf-8") as fp:
        if 'susecloud.net' in fp.read():
            try:
                cloud_register_metadata = \
                    get_regionsrv_client_file_location(root_path)
            except DistMigrationZypperMetaDataException as issue:
                log.error(
                    'Failed locating regionsrv-client cache files: {0}'.format(
                        issue
                    )
                )
                raise

    zypper_log_file = os.sep.join(
        [root_path, 'var', 'log', 'zypper.log']
    )
    if os.path.exists(zypper_log_file):
        try:
            zypper_host_log_file = zypper_log_file.replace(root_path, '')
            if not os.path.exists(zypper_host_log_file):
                with open(zypper_host_log_file, 'w'):
                    # we bind mount the system zypper log file
                    # but the mount target does not exist.
                    # Create it as empty file prior bind mounting
                    pass
                Command.run(
                    ['mount', '--bind', zypper_log_file, zypper_host_log_file]
                )
        except Exception as issue:
            log.warning(
                'Bind mounting zypper log file failed with: {0}'.format(issue)
            )
    try:
        # log network info as network-online.target is done at this point
        log_network_details()
        log.info('Running prepare service')
        system_mount = Fstab()
        system_mount.read(
            Defaults.get_system_mount_info_file()
        )
        log.info('Bind mounting /etc/zypp')
        Command.run(
            ['mount', '--bind', zypp_metadata, '/etc/zypp']
        )
        system_mount.add_entry(
            zypp_metadata, '/etc/zypp'
        )
        log.info('Bind mounting /usr/lib/zypp/plugins')
        Command.run(
            [
                'mount', '--bind', zypp_plugins_services,
                '/usr/lib/zypp/plugins/services'
            ]
        )
        system_mount.add_entry(
            zypp_plugins_services, '/usr/lib/zypp/plugins/services'
        )
        if os.path.exists(cloud_register_metadata):
            log.info(
                'Bind mounting {0} from {1}'.format(
                    cache_cloudregister_path, cloud_register_metadata
                )
            )
            Path.create(cache_cloudregister_path)
            Command.run(
                [
                    'mount', '--bind', cloud_register_metadata,
                    cache_cloudregister_path
                ]
            )
            update_smt_cache = '/usr/sbin/updatesmtcache'
            if os.path.isfile(update_smt_cache):
                log.info('Updating SMT cache')
                Command.run(
                    [update_smt_cache]
                )
        system_mount.export(
            Defaults.get_system_mount_info_file()
        )
        # Check if system is registered
        migration_config = MigrationConfig()
        if migration_config.is_zypper_migration_plugin_requested():
            if not SUSEConnect.is_registered():
                message = 'System not registered. Aborting migration.'
                log.error(message)
                raise DistMigrationSystemNotRegisteredException(
                    message
                )
    except Exception as issue:
        log.error(
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


def update_regionsrv_setup(root_path, suse_cloud_regionsrv_setup):
    """
    Note: This method is specific to the SUSE Public Cloud Infrastructure

    Update regionserverclnt.cfg config file when running in the Azure
    Cloud. The method modifies the pre-configured azuremetadata call
    in a way that it passes the root device as option to skip the
    automated detection of that device. The implementation in azuremetadata
    does not work when used inside of the special migration live system.
    """
    regionsrv_setup = ConfigParser()
    regionsrv_setup.read(suse_cloud_regionsrv_setup)
    dataProvider = regionsrv_setup.get('instance', 'dataProvider')
    if 'azuremetadata' in dataProvider:
        root_disk_device = get_root_disk_device(root_path)
        if root_disk_device:
            dataProvider += ' --device {0}'.format(root_disk_device)
            regionsrv_setup.set('instance', 'dataProvider', dataProvider)
            with open(suse_cloud_regionsrv_setup, 'w') as regionsrv_file:
                regionsrv_setup.write(regionsrv_file)


def get_root_disk_device(root_path):
    """
    Find unix disk device which is associated with the
    root mount point given in root_path
    """
    root_device = Command.run(
        [
            'findmnt', '--first', '--noheadings',
            '--output', 'SOURCE', '--mountpoint', root_path
        ]
    ).output
    if root_device:
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


def get_regionsrv_client_file_location(root_path):
    """
    Find the correct path for the cloud-regionsrv-client cache files
    as the location moves from /var/lib/cloudregister
    (pre cloud-regionsrv-client-10.0.4) to /var/cache/cloudregister
    (post cloud-regionsrv-client-10.0.4)
    """
    for cloud_register_path in [
        os.sep.join([root_path, 'var', 'cache', 'cloudregister']),
        os.sep.join([root_path, 'var', 'lib', 'cloudregister'])
    ]:
        if os.path.isdir(cloud_register_path) and \
                any('SMT' in x for x in os.listdir(cloud_register_path)):
            return cloud_register_path
    raise DistMigrationZypperMetaDataException(
        'No cloud-regionsrv-client cache files found in '
        '/var/cache/cloudregister or /var/lib/cloudregister'
    )
