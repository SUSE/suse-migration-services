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
from suse_migration_services.defaults import Defaults

from suse_migration_services.exceptions import (
    DistMigrationSUSEConnectException,
    DistMigrationZypperMetaDataException
)


def main():
    """
    DistMigration prepare for migration

    Prepare migration live system to allow zypper migration to
    perform its job. The zypper migration process contacts one
    of SUSE's subscription management services SCC/RMT/SMT
    and switches the repository setup as it is required for
    the migration process. To do that the migration live
    system has to import /etc/SUSEConnect from the migration
    host as well as bind mount /etc/zypp from the migration host
    to the migration live system. The repo setup in /etc/zypp
    will be permanently changed to the new distribution and
    must also be available on the migration live system during
    the process.
    """
    root_path = Defaults.get_system_root_path()

    suse_connect_setup = os.sep.join(
        [root_path, 'etc', 'SUSEConnect']
    )
    if not os.path.exists(suse_connect_setup):
        raise DistMigrationSUSEConnectException(
            'Could not find {0} on migration host'.format(suse_connect_setup)
        )

    shutil.copy(
        suse_connect_setup, '/etc/SUSEConnect'
    )

    zypp_metadata = os.sep.join(
        [root_path, 'etc', 'zypp']
    )
    try:
        Command.run(
            ['mount', '--bind', zypp_metadata, '/etc/zypp']
        )
    except Exception as issue:
        raise DistMigrationZypperMetaDataException(
            'Preparation of zypper metadata failed with {0}'.format(
                issue
            )
        )
