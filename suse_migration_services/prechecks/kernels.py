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
"""Checks the multiversion.kernels setting and the presence of multiple kernels

Check to see if multiversion.kernels are enabled in /etc/zypp/zypp.conf and
if there is more than one kernel currently installed. If detected, a warning is reported
as multiversion.kernels needs to be disabled and old kernels cleaned up before
a migration can be started."""

import configparser
import logging
import os
import re

from suse_migration_services.defaults import Defaults
from suse_migration_services.command import Command
from suse_migration_services.exceptions import DistMigrationCommandException


def multiversion_and_multiple_kernels(fix=False, migration_system=False):
    """Check for the number of installed kernels"""

    log = logging.getLogger(Defaults.get_migration_log_name())

    multiversion_settings(fix, migration_system, log)
    multiple_kernels_installed(fix, migration_system, log)


def multiversion_settings(fix, migration_system, log):
    """Check the settings in etc/zypp/zypp.conf"""

    config = configparser.ConfigParser()
    _config_path = Defaults.get_zypp_config_path()
    if migration_system:
        _config_path = Defaults.get_system_root_path() + Defaults.get_zypp_config_path()

    config.read(_config_path)

    kernel_multi_version_enabled = config.get('main', 'multiversion', fallback=None)

    if not kernel_multi_version_enabled:
        log.info(
            "Could not find the config option 'multiversion' in "
            "/etc/zypp/zypp.conf. Skipping check for "
            "'multiversion.kernels'"
        )
    elif 'kernel' in kernel_multi_version_enabled:
        kernel_multi_version_settings = config.get('main', 'multiversion.kernels', fallback=None)

        log.info(
            "The config option 'multiversion' in /etc/zypp/zypp.conf "
            "includes the keyword 'kernel.' The current value is set "
            "as \n'multiversion = %s'.\nChecking the config option "
            "'multiversion.kernels' to see if multiple kernels are "
            "also enabled",
            kernel_multi_version_enabled,
        )
        if not kernel_multi_version_settings:
            log.warning(
                'Missing multiversion.kernels setting in zypp.conf. '
                'Please ensure it is set as:\n'
                "'multiversion.kernels = latest,running'"
            )
        elif set(kernel_multi_version_settings.split(',')) != {'running', 'latest'}:
            if fix:
                log.info(
                    "The '--fix' option was provided, "
                    "setting 'multiversion.kernels = latest,running' "
                )
                existing = 'multiversion.kernels = ' + kernel_multi_version_settings
                correction = 'multiversion.kernels = latest,running'
                sed_arg = 's/' + existing + '/' + correction + '/'
                try:
                    Command.run(["sed", "-i", sed_arg, Defaults.get_zypp_config_path()])
                except DistMigrationCommandException:
                    log.error("ERROR: Unable to update /etc/zypp/zypp.conf")
            else:
                log.warning(
                    "The config option multiversion.kernels is not set "
                    "correctly in /etc/zypp/zypp.conf. It is currrently "
                    "set as:\n\n'multiversion.kernels = %s'.\n\n"
                    "Please ensure it is set as:\n\n"
                    "'multiversion.kernels = latest,running'\n",
                    kernel_multi_version_settings,
                )


def multiple_kernels_installed(fix, migration_system, log):
    """Check for multiple kernels installed"""

    kernel_type = 'kernel-default'
    running_kernel_path = os.sep + Defaults.get_target_kernel()
    if migration_system:
        running_kernel_path = Defaults.get_system_root_path() + running_kernel_path
    running_kernel = os.readlink(running_kernel_path)

    if 'azure' in running_kernel:
        kernel_type = 'kernel-azure'

    rpm_query_command = ["rpm", "-qa", kernel_type]
    if migration_system:
        rpm_query_command = ["chroot", Defaults.get_system_root_path(), "rpm", "-qa", kernel_type]

    installed_kernels = Command.run(rpm_query_command).output.splitlines()

    if len(installed_kernels) > 1:
        log.info(
            'Multiple kernels have been detected on the system:\n\n' '%s\n',
            '\n'.join(installed_kernels),
        )
        if fix:
            log.info("The '--fix' option was provided, removing old kernels")
            running_kernel_version = (
                kernel_type + re.search(r'([0-9.-]*(?=[-][a-zA-Z]))', running_kernel).group()
            )
            rpm_erase_command = ["rpm", "-e"]
            if migration_system:
                rpm_erase_command = ["chroot", Defaults.get_system_root_path(), "rpm", "-e"]
            for _ in installed_kernels:
                if running_kernel_version not in _:
                    log.info('Removing: %s', _)
                    try:
                        rpm_erase_command.append(_)
                        Command.run(rpm_erase_command)
                    except DistMigrationCommandException:
                        log.error("ERROR: Unable to remove old kernel(s)")
        else:
            log.warning(
                'Please remove all kernels other than the currrent ' 'running kernel: %s\n',
                running_kernel,
            )
