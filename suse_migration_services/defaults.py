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


class Defaults(object):
    """
    **Implements default values**

    Provides class methods for default values
    """
    @classmethod
    def get_system_root_path(self):
        return '/system-root'

    @classmethod
    def get_migration_config_file(self):
        return '/etc/migration-config.yml'

    @classmethod
    def get_migration_log_file(self):
        return os.sep.join(
            [self.get_system_root_path(), 'var/log/distro_migration.log']
        )

    @classmethod
    def get_system_migration_custom_config_file(self):
        return os.sep.join(
            [self.get_system_root_path(), 'etc/sle-migration-service.yml']
        )

    @classmethod
    def get_system_mount_info_file(self):
        return '/etc/system-root.fstab'

    @classmethod
    def get_grub_config_file(self):
        return 'boot/grub2/grub.cfg'

    @classmethod
    def get_target_kernel(self):
        return 'boot/vmlinuz'

    @classmethod
    def get_target_initrd(self):
        return 'boot/initrd'

    @classmethod
    def get_ssh_keys_paths(self):
        return [
            self._get_ssh_keys_path(self, 'home/*'),
            self._get_ssh_keys_path(self, 'root')
        ]

    @classmethod
    def get_migration_ssh_file(self):
        return '/home/migration/.ssh/authorized_keys'

    def _get_ssh_keys_path(self, prefix_path):
        return os.sep.join(
            [self.get_system_root_path(), prefix_path, '.ssh/authorized_keys']
        )

    @classmethod
    def get_system_ssh_host_keys_glob_path(self):
        return os.sep.join(
            [self.get_system_root_path(), 'etc/ssh/ssh_host_*']
        )

    @classmethod
    def get_system_sshd_config_path(self):
        return '/etc/ssh/sshd_config'
