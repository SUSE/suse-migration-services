# Copyright (c) 2023 SUSE Linux LLC.  All rights reserved.
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
"""systemd service to install the shim package and update the bootloader"""
import logging

# project
from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger
from suse_migration_services.zypper import Zypper


class UpdateBootLoader:
    def __init__(self):
        """
        DistMigration install the shim pacakge, enable "Secure boot"
        and update the bootloader
        """
        Logger.setup()
        self.log = logging.getLogger(Defaults.get_migration_log_name())
        self.root_path = Defaults.get_system_root_path()

    def perform(self):
        self.log.info('Running update bootloader service')
        self.log.info('Installing the shim package')
        self.install_shim_package()
        self.log.info('Updating the shimbootloader')
        self.install_secure_bootloader()
        self.log.info('Updating the bootloader')
        self.update_bootloader_config()

    def install_shim_package(self):
        """
        Install the shim package
        """
        Zypper.run(
            [
                '--no-cd',
                '--non-interactive',
                '--gpg-auto-import-keys',
                '--root', self.root_path,
                'install',
                '--auto-agree-with-licenses',
                '--allow-vendor-change',
                '--download', 'in-advance',
                '--replacefiles',
                '--allow-downgrade',
                'shim',
            ]
        )

    def install_secure_bootloader(self):
        """
        Perform shim-install from inside the upgraded system.
        If the system is not suitable to be setup for shim e.g.
        not EFI based, we don't consider it as a fatal error
        and continue while keeping the log information about the
        attempt.
        """
        Command.run(
            ['chroot', self.root_path, 'shim-install', '--removable'],
            raise_on_error=False
        )

    def update_bootloader_config(self):
        """
        Perform update-bootloader from inside of the upgraded system
        """
        Command.run(
            ['chroot', self.root_path, '/sbin/update-bootloader', '--reinit']
        )


def main():
    update_bootloader = UpdateBootLoader()
    update_bootloader.perform()
