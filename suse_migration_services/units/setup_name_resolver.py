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
import logging
import os

# project
from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger
from suse_migration_services.resolv_conf import ResolvConf


class SetupNameResolver:
    def __init__(self):
        """
        DistMigration setup name resolver

        Setup /etc/resolv.conf by importing the resolver configuration
        from the migration host
        """
        Logger.setup()
        self.log = logging.getLogger(Defaults.get_migration_log_name())
        self.root_path = Defaults.get_system_root_path()
        self.resolv_conf = ResolvConf(
            self.root_path,
            os.path.normpath(os.sep.join([self.root_path, 'etc'])),
            '/etc'
        )

    def perform(self):
        self.resolv_conf.prepare_resolv_conf()


def main():
    name_resolver = SetupNameResolver()
    name_resolver.perform()
