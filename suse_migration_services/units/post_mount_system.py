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
import os
import shutil
import glob

# project
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger
from suse_migration_services.migration_config import MigrationConfig
from suse_migration_services.command import Command


class PostMountSystem:
    def __init__(self):
        """
        DistMigration post mount actions

        Preserve custom data file(s) e.g udev rules from the system
        to be migrated to the live migration system and activate
        those file changes to become effective
        """
        Logger.setup()
        self.log = logging.getLogger(Defaults.get_migration_log_name())
        self.root_path = Defaults.get_system_root_path()
        self.systemd_default_link_path = '/etc/systemd/network/99-default.link'

    def perform(self):
        self.log.info('Running post mount actions')

        # Remove 99-default.link that may have been installed
        # to disable predictable naming scheme for network interfaces
        if os.path.isfile(self.systemd_default_link_path):
            os.remove(self.systemd_default_link_path)

        migration_config = MigrationConfig()
        preserve_info = migration_config.get_preserve_info()
        if preserve_info:
            for _, preserve_files in preserve_info.items():
                for preserve_file in preserve_files:
                    source_glob = os.path.normpath(os.sep.join([self.root_path, preserve_file]))
                    for source_file in glob.glob(source_glob):
                        target_dir = os.path.dirname(source_file)[len(self.root_path) :]
                        self.log.info('Copy file: {0} to: {1}'.format(source_file, target_dir))
                        if not os.path.exists(target_dir):
                            Command.run(['mkdir', '-p', target_dir])
                        shutil.copy(source_file, target_dir)
            if 'rules' in preserve_info.keys():
                Command.run(['udevadm', 'control', '--reload'])
                Command.run(['udevadm', 'trigger', '--type=subsystems', '--action=add'])
                Command.run(['udevadm', 'trigger', '--type=devices', '--action=add'])
            if 'sysctl' in preserve_info.keys():
                Command.run(['sysctl', '--system'])


def main():
    post_mount_os = PostMountSystem()
    post_mount_os.perform()
