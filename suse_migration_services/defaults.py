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
        return 'boot/vmlinuz'

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
            keys, values = zip(
                *[
                    (key.lower(), value.strip('\'"')) for (key, value) in (
                        line.strip().split('=', 1) for line in
                        handle.read().strip().split(os.linesep)
                    )
                ]
            )
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
        return os.sep.join(
                [Defaults.get_system_root_path(), '/etc/default/grub']
        )
