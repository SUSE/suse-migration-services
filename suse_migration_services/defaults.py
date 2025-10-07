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
import platform
from collections import namedtuple


class Defaults:
    """
    **Implements default values**

    Provides class methods for default values
    """
    @staticmethod
    def get_system_root_path():
        return '/system-root'

    @staticmethod
    def get_migration_config_file():
        return '/etc/migration-config.yml'

    @staticmethod
    def get_migration_host_config_file():
        return '/etc/sle-migration-service.yml'

    @staticmethod
    def get_migration_config_dir():
        return '/etc/migration-config.d'

    @staticmethod
    def get_migration_log_name():
        return 'suse-migration'

    @staticmethod
    def get_migration_exit_code_file():
        return '/var/log/distro_migration.exitcode'

    @staticmethod
    def get_migration_log_file(system_root=True):
        migration_log_file = 'var/log/distro_migration.log'

        if system_root:
            migration_log_file = os.sep.join(
                [Defaults.get_system_root_path(), migration_log_file]
            )
        else:
            migration_log_file = os.sep + migration_log_file
        return migration_log_file

    @staticmethod
    def get_system_migration_custom_config_file():
        return os.sep.join(
            [Defaults.get_system_root_path(), 'etc/sle-migration-service.yml']
        )

    @staticmethod
    def get_system_mount_info_file():
        return '/etc/system-root.fstab'

    @staticmethod
    def get_grub_config_file():
        return 'boot/grub2/grub.cfg'

    @staticmethod
    def get_target_kernel():
        machine = platform.machine()
        if machine == "x86_64":
            return 'boot/vmlinuz'
        elif machine == "aarch64":
            return 'boot/Image'
        elif machine == "ppc64le":
            return 'boot/vmlinux'
        elif machine == "s390x":
            return 'boot/image'
        else:
            raise NotImplementedError(
                f'get_target_kernel not implemented for machine type {machine}')

    @staticmethod
    def get_target_initrd():
        return 'boot/initrd'

    @staticmethod
    def get_ssh_keys_paths():
        return [
            Defaults._get_ssh_keys_path('home/*'),
            Defaults._get_ssh_keys_path('root')
        ]

    @staticmethod
    def get_migration_ssh_file():
        return '/home/migration/.ssh/authorized_keys'

    @staticmethod
    def _get_ssh_keys_path(prefix_path):
        return os.sep.join(
            [
                Defaults.get_system_root_path(), prefix_path,
                '.ssh/authorized_keys'
            ]
        )

    @staticmethod
    def get_system_ssh_host_keys_glob_path():
        return os.sep.join(
            [Defaults.get_system_root_path(), 'etc/ssh/ssh_host_*']
        )

    @staticmethod
    def get_system_sshd_config_path():
        return '/etc/ssh/sshd_config'

    @staticmethod
    def get_os_release():
        with open('/etc/os-release', 'r') as handle:
            valid_pairs = []
            # Read the whole file, strip leading/trailing whitespace from the content,
            # then split into lines.
            raw_lines = handle.read().strip().split(os.linesep)

            for line_text in raw_lines:
                stripped_line = line_text.strip()

                # Skip empty lines and lines that are comments
                if not stripped_line or stripped_line.startswith('#'):
                    continue

                parts = stripped_line.split('=', 1)
                if len(parts) == 2:
                    key, value = parts
                    valid_pairs.append((key.lower(), value.strip('\'"')))
                # else: malformed line (e.g., no '='), ignore it as per os-release behavior

            if not valid_pairs:
                # Handle cases where /etc/os-release is empty or contains only comments/invalid lines
                return namedtuple('OSRelease', [])()

            keys, values = zip(*valid_pairs)
            return namedtuple('OSRelease', keys)(*values)

    @staticmethod
    def get_proxy_path():
        return '/etc/sysconfig/proxy'

    @staticmethod
    def get_zypp_config_path():
        return '/etc/zypp/zypp.conf'

    @staticmethod
    def get_zypp_gen_solver_test_case():
        return ''

    @staticmethod
    def get_grub_default_file():
        return os.path.normpath(
            os.sep.join(
                [Defaults.get_system_root_path(), '/etc/default/grub']
            )
        )
