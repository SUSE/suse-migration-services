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
# project
from suse_migration_services.command import Command
from suse_migration_services.logger import log
from suse_migration_services.defaults import Defaults


class SUSEConnect:
    @staticmethod
    def is_registered():
        """
        Run SUSEConnect to list available extensions and modules.
        If that list exists the system is registered. If this
        information cannot be provided for some reason, the system
        is considered unregistered
        """
        root_path = Defaults.get_system_root_path()
        extensions_cmd_result = Command.run(
            ['chroot', root_path, 'SUSEConnect', '--list-extensions'],
            raise_on_error=False
        )
        result = True
        if extensions_cmd_result.returncode != 0:
            log.error(extensions_cmd_result.output)
            result = False

        return result
