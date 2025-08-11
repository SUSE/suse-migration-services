# Copyright (c) 2022 SUSE Linux LLC.  All rights reserved.
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
"""systemd service to build a host independant initrd"""
import logging

# project
from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger
from suse_migration_services.migration_config import MigrationConfig

from suse_migration_services.exceptions import (
    DistMigrationCommandException
)


def main():
    """
    DistMigration create a new initrd with added modules

    Run dracut to build a new initrd that includes multipath modules
    """
    Logger.setup()
    log = logging.getLogger(Defaults.get_migration_log_name())
    log.info('Running initrd creation service')

    if MigrationConfig().is_host_independent_initd_requested():
        log.info('Creating a new host independent initrd')
        root_path = Defaults.get_system_root_path()

        dracut_bind_mounts(root_path)
        run_dracut(root_path)


def dracut_bind_mounts(root_path,):
    """Function to do bind mounts needed before running dracut"""

    log = logging.getLogger(Defaults.get_migration_log_name())

    BIND_DIRS = ['/dev', '/proc', '/sys']

    for bind_dir in BIND_DIRS:
        try:
            log.info(
                'Running mount --bind {0} {1}'.format(bind_dir, root_path + bind_dir)
            )
            Command.run(
                [
                    'mount',
                    '--bind',
                    bind_dir,
                    root_path + bind_dir
                ]
            )
        except Exception as issue:
            log.error(
                'Unable to mount: {0}'.format(issue)
            )
            raise DistMigrationCommandException(
                'Unable to mount: {0}'.format(
                    issue
                )
            ) from issue


def run_dracut(root_path):
    """Function run dracut"""

    log = logging.getLogger(Defaults.get_migration_log_name())

    try:
        log.info(
            'Running chroot {0} dracut --no-kernel --no-host-only --no-hostonly-cmdline'
            '--regenerate-all --logfile /tmp/host_independent_initrd.log -f'.format(root_path)
        )
        Command.run(
            [
                'chroot',
                root_path,
                'dracut',
                '--no-host-only',
                '--no-hostonly-cmdline',
                '--regenerate-all',
                '--logfile',
                '/tmp/host_independent_initrd.log',
                '-f'
            ]
        )
        Command.run(
            [
                'chroot',
                root_path,
                'cat',
                '/tmp/host_independent_initrd.log',
                '>> /var/log/distro_migration.log'
            ]
        )
        Command.run(
            [
                'chroot',
                root_path,
                'rm',
                '/tmp/host_independent_initrd.log'
            ]
        )
    except Exception as issue:
        log.error(
            'Unable to create new initrd with dracut: {0}'.format(issue)
        )
        raise DistMigrationCommandException(
            'Failed to create new initrd: {0}'.format(
                issue
            )
        ) from issue
