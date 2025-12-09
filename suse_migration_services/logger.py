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
import logging

# project
from suse_migration_services.path import Path
from suse_migration_services.defaults import Defaults


class Logger:
    @staticmethod
    def setup(system_root=True):
        logger = logging.getLogger(Defaults.get_migration_log_name())
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            log_file = Defaults.get_migration_log_file(system_root)
            Path.create(os.path.dirname(log_file))

            log_to_file = logging.FileHandler(log_file)
            log_to_file.setLevel(logging.INFO)

            log_to_stream = logging.StreamHandler()
            log_to_stream.setLevel(logging.INFO)

            logger.addHandler(log_to_stream)
            logger.addHandler(log_to_file)
