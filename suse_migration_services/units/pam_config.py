# Copyright (c) 2025 SUSE Linux LLC.  All rights reserved.
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
import glob
import os
import re

from suse_migration_services.defaults import Defaults
from suse_migration_services.logger import Logger


class PamConfig:
    def __init__(self):
        """
        DistMigration update PAM configuration

        pam_unix_*.so have been migrated to pam_unix.so. We need to update
        all configuration under /etc/pam.d to make them refers to the new
        shared object.
        """
        Logger.setup()
        self.log = logging.getLogger(Defaults.get_migration_log_name())

    def perform(self):
        self.log.info("Scanning /etc/pam.d")
        pam_unix_regexp = re.compile(
            r"pam_unix_(auth|acct|session|passwd)\.so"
        )
        system_root = Defaults.get_system_root_path()
        config_dir_path = os.path.join(system_root, 'etc/pam.d/*')
        for config_file in glob.glob(config_dir_path):
            self.log.info(
                'Migration PAM configuration file {0}'.format(config_file)
            )
            with open(config_file, 'r') as f:
                content = f.read()
            content = pam_unix_regexp.sub('pam_unix.so', content)
            with open(config_file, 'w') as f:
                f.write(content)


def main():
    pam_setup = PamConfig()
    pam_setup.perform()
