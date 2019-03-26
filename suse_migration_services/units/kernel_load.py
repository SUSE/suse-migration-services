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
import re
import os
import shutil

# project
from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import log
from suse_migration_services.path import Path

from suse_migration_services.exceptions import (
    DistMigrationKernelRebootException
)


def main():
    """
    DistMigration load new kernel for kexec reboot

    Loads the new kernel/initrd after migration for system reboot
    """
    root_path = Defaults.get_system_root_path()

    target_kernel = os.sep.join([root_path, Defaults.get_target_kernel()])
    target_initrd = os.sep.join([root_path, Defaults.get_target_initrd()])
    kexec_boot_data = '/var/tmp/kexec'
    Path.create(kexec_boot_data)
    shutil.copy(
        target_initrd, kexec_boot_data
    )
    try:
        log.info('Running kernel load service')
        log.info('Loading the target kernel')
        Command.run(
            [
                'kexec',
                '--load', target_kernel,
                '--initrd', os.sep.join(
                    [kexec_boot_data, os.path.basename(target_initrd)]
                ),
                '--command-line', _get_cmdline(os.path.basename(target_kernel))
            ]
        )
    except Exception as issue:
        log.error('Kernel load service raised exception: {0}', format(issue))
        raise DistMigrationKernelRebootException(
            'Failed to load kernel/initrd into memory: {0}'.format(
                issue
            )
        )


def _get_cmdline(kernel_name):
    log.info('Getting cmdline for {0}'.format(kernel_name))
    grub_config_file_path = os.sep.join(
        [Defaults.get_system_root_path(), Defaults.get_grub_config_file()]
    )
    if not os.path.exists(grub_config_file_path):
        log.error(
            'kernel load service was not able to find'
            '{0}'.format(grub_config_file_path)
        )
        raise DistMigrationKernelRebootException(
            'Could not find {0} to load the kernel options'.format(
                grub_config_file_path
            )
        )
    with open(grub_config_file_path) as grub_config_file:
        grub_content = grub_config_file.read()
    pattern = r'(?<=linux)[ \t]+{0}([{1}|boot/{1}].*)'.format(os.sep, kernel_name)
    cmd_line = re.findall(pattern, grub_content)[0]
    cmd_line = cmd_line.split()
    cmd_line_options = []
    for option in cmd_line:
        if kernel_name not in option:
            cmd_line_options.append(option)
    return ' '.join(cmd_line_options)
