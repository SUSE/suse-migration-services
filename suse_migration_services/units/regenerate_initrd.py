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
import os
import logging

# project
from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger
from suse_migration_services.migration_config import MigrationConfig

from suse_migration_services.exceptions import DistMigrationCommandException


class RegenerateBootImage:
    def __init__(self):
        """
        DistMigration create a new initrd with added modules

        Run dracut to build a new initrd taking into account the
        dracut module configuration at call time
        """
        Logger.setup()
        self.log = logging.getLogger(Defaults.get_migration_log_name())
        self.root_path = Defaults.get_system_root_path()

    def perform(self):
        self.log.info('Running initrd creation service')
        if MigrationConfig().is_host_independent_initd_requested():
            self.log.info('Creating a new host independent initrd')
            self._dracut_bind_mounts()
            self._run_dracut()
        else:
            self.log.info('No action needed, dracut was called during installation')

    def _dracut_bind_mounts(self):
        """
        Function to do bind mounts needed before running dracut
        """
        for bind_dir in ['/dev', '/proc', '/sys']:
            try:
                self.log.info(
                    'Running mount --bind {0} {1}'.format(bind_dir, self.root_path + bind_dir)
                )
                Command.run(
                    [
                        'mount',
                        '--bind',
                        bind_dir,
                        os.path.normpath(os.sep.join([self.root_path, bind_dir])),
                    ]
                )
            except Exception as issue:
                message = 'Unable to mount: {0}'.format(issue)
                self.log.error(message)
                raise DistMigrationCommandException(message)

    def _run_dracut(self):
        """
        Call dracut as chroot operation
        """
        try:
            self.log.info('Running dracut service')
            log_file = Defaults.get_migration_log_file(system_root=False)
            command_string = ' '.join(
                [
                    'chroot',
                    self.root_path,
                    'dracut',
                    '--force',
                    '--verbose',
                    '--no-host-only',
                    '--no-hostonly-cmdline',
                    '--regenerate-all',
                    '&>>',
                    log_file,
                ]
            )
            Command.run(['bash', '-c', command_string])
        except Exception as issue:
            message = 'Failed to create new initrd: {}'.format(issue)
            self.log.error(message)
            raise DistMigrationCommandException(message)


def main():
    boot_image = RegenerateBootImage()
    boot_image.perform()
