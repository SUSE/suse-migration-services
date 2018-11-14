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
    def get_system_mount_info_file(self):
        return '/etc/system-root.fstab'

    @classmethod
    def get_grub_path(self):
        return '/boot/grub2/grub.cfg'
