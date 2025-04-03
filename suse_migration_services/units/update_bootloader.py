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


def main():
    """
    DistMigration install the shim pacakge, enable "Secure boot"
    and update the bootloader
    """
    Logger.setup()
    log = logging.getLogger(Defaults.get_migration_log_name())

    root_path = Defaults.get_system_root_path()

    log.info('Installing the shim package')
    install_shim_package(root_path)
    log.info('Updating the shimbootloader')
    install_secure_bootloader(root_path)
    log.info('Updating the bootloader')
    update_bootloader_config(root_path)


def install_shim_package(root_path):
    """
    Install the shim package
    """
    bash_command = ' '.join(
        [
            'zypper',
            '--no-cd',
            '--non-interactive',
            '--gpg-auto-import-keys',
            '--root', root_path,
            'in',
            '--auto-agree-with-licenses',
            '--allow-vendor-change',
            '--download', 'in-advance',
            '--replacefiles',
            '--allow-downgrade',
            'shim',
            '&>>', Defaults.get_migration_log_file()
        ]
    )
    Command.run(
        ['bash', '-c', bash_command]
    )


def install_secure_bootloader(root_path):
    """
    Perform shim-install from inside the upgraded system
    """
    Command.run(
        ['chroot', root_path, 'shim-install', '--removable']
    )


def update_bootloader_config(root_path):
    """
    Perform update-bootloader from inside of the upgraded system
    """
    Command.run(
        ['chroot', root_path, '/sbin/update-bootloader', '--reinit']
    )
