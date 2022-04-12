# Copyright (c) 2022
#
# SUSE Linux LLC.  All rights reserved.
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
"""Pre-Checks multiversion kernels

Check to see if multiversion.kernels are enabled in /etc/zypp/zypp.conf and
if there is more than one kernel currently installed. If detected a warning is reported
as multiversion.kernels needs to be disabled and old kernels cleaned up before
migrationg."""

# import os
import configparser
import logging

from suse_migration_services.defaults import Defaults
from suse_migration_services.command import Command


def multiversion_kernels():
    """Check for the number of installed kernels"""
    log = logging.getLogger(Defaults.get_migration_log_name())

    config = configparser.ConfigParser()
    config.read(Defaults.get_zypp_config_path())

    current_settings = config.get('main', 'multiversion.kernels', fallback=None)

    if not current_settings:
        log.warning('Missing multiversion.kernels setting in zypp.conf. '
                    'Please ensure it is set as:\n'
                    "'multiversion.kernels = latest,running'")
    elif current_settings != 'latest,running':
        log.warning('The config option multiversion.kernels is not set '
                    'correctly in /etc/zypp/zypp.conf. It is currrently '
                    'set as \n%s.\nPlease ensure it is set as:\n'
                    "'multiversion.kernels = latest,running'",
                    current_settings)

    kernel_type = 'kernel-default'
    running_kernel = Command.run(["uname", "-r"])

    if 'azure' in running_kernel.output:
        kernel_type = 'kernel-azure'

    installed_kernels = Command.run(["rpm", "-qa", kernel_type])
    count = len(installed_kernels.output.splitlines())

    if count > 1:
        log.warning(
            'Multiple kernels have been detected on the system:\n'
            '%s\n'
            'Please remove all kernels other than the currrent running kernel, '
            '%s\n', installed_kernels.output, running_kernel.output)
