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
import os
import shutil

# project
from suse_migration_services.command import Command
from suse_migration_services.fstab import Fstab
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import log

from suse_migration_services.exceptions import (
    DistMigrationZypperMetaDataException
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
    trust_anchors = os.sep.join(
        [root_path, 'usr', 'share', 'pki', 'trust', 'anchors']
    )
    if os.path.exists(suse_connect_setup):
        shutil.copy(
            suse_connect_setup, '/etc/SUSEConnect'
        )
    if os.path.exists(suse_cloud_regionsrv_setup):
        shutil.copy(
            suse_cloud_regionsrv_setup, '/etc/regionserverclnt.cfg'
        )
    if os.path.exists(hosts_setup):
        shutil.copy(
            hosts_setup, '/etc/hosts'
        )
    if os.path.exists(trust_anchors):
        certificates = os.listdir(trust_anchors)
        if certificates:
            for cert in certificates:
                log.info(
                    'Importing certificate: {0}'.format(cert)
                )
                shutil.copy(
                    os.sep.join([trust_anchors, cert]),
                    '/usr/share/pki/trust/anchors/'
                )
            log.info('Update certificate pool')
            Command.run(
                ['update-ca-certificates']
            )

    zypp_metadata = os.sep.join(
        [root_path, 'etc', 'zypp']
    )
    zypp_plugins = os.sep.join(
        [root_path, 'usr', 'lib', 'zypp', 'plugins']
    )
    dev_mount_point = os.sep.join(
        [root_path, 'dev']
    )
    proc_mount_point = os.sep.join(
        [root_path, 'proc']
    )
    sys_mount_point = os.sep.join(
        [root_path, 'sys']
    )
    try:
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
            ['mount', '--bind', zypp_plugins, '/usr/lib/zypp/plugins']
        )
        system_mount.add_entry(
            zypp_plugins, '/usr/lib/zypp/plugins'
        )
        log.info('Mounting kernel file systems inside {0}'.format(root_path))
        Command.run(
            ['mount', '-t', 'devtmpfs', 'devtmpfs', dev_mount_point]
        )
        system_mount.add_entry(
            'devtmpfs', dev_mount_point
        )
        Command.run(
            ['mount', '-t', 'proc', 'proc', proc_mount_point]
        )
        system_mount.add_entry(
            '/proc', proc_mount_point
        )
        Command.run(
            ['mount', '-t', 'sysfs', 'sysfs', sys_mount_point]
        )
        system_mount.add_entry(
            'sysfs', sys_mount_point
        )
        system_mount.export(
            Defaults.get_system_mount_info_file()
        )
    except Exception as issue:
        log.error(
            'Preparation of zypper metadata failed with {0}'.format(
                issue
            )
        )
        log.info('Unmounting kernel file systems, if any')
        for entry in reversed(system_mount.get_devices()):
            Command.run(
                ['umount', entry.mountpoint], raise_on_error=False
            )
        raise DistMigrationZypperMetaDataException(
            'Preparation of zypper metadata failed with {0}'.format(
                issue
            )
        )
