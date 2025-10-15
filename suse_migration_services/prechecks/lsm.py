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
"""
Call prechecks for LSM migration (apparmor to selinux)
"""
import logging
import json
import os
import shutil
from textwrap import dedent

from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults

# find /etc/apparmor.d/ | wc -l
DEFAULT_ETC_FILE_COUNT = 263
# aa-status --json | jq '.profiles | length'
DEFAULT_PROFILE_COUNT = 58

ADDITIONAL_AA_PROFILES = [
    "colord",
    "dnsdist",
    "git-web",
    "golang-github-lusitaniae-apache_exporter",
    "haproxy",
    "libvirt-daemon-common",
    "libvirt-daemon-driver-libxl",
    "libvirt-daemon-driver-qemu",
    "libvirt-daemon",
    "mlocate",
    "monitoring-plugins-cups",
    "monitoring-plugins-dhcp",
    "monitoring-plugins-disk",
    "monitoring-plugins-icmp",
    "monitoring-plugins-ide_smart",
    "monitoring-plugins-load",
    "monitoring-plugins-ntp_time",
    "monitoring-plugins-ping",
    "monitoring-plugins-procs",
    "monitoring-plugins-ssh",
    "monitoring-plugins-swap",
    "monitoring-plugins-userso",
]

log = logging.getLogger(Defaults.get_migration_log_name())


def check_lsm(migration_system=False):
    if migration_system:
        # only relevant on the system that is being migrated
        log.info('Skipped LSM migration checks.')
        return

    if _apparmor_enabled():
        if not shutil.which('aa-status'):
            # no aa-status found, run a primitive check for apparmor files
            _apparmor_primitive_check()
            return
        try:
            aa_status_output = Command.run(
                ['aa-status', '--json']
            ).output
            if aa_status_output:
                aa_data = json.loads(aa_status_output)

                manual_check_needed = _apparmor_standard_profiles_modified()
                if _apparmor_additional_profiles(aa_data) \
                   and _apparmor_extended_profiles_modified():
                    manual_check_needed = True

                if manual_check_needed:
                    message = dedent('''\n
                        Non-default AppArmor setup detected,
                        please review the details above.
                    ''')
                    log.error(message)
        except Exception as issue:
            log.warn('aa-status failed with: {}'.format(issue))
            log.warn('Skipping LSM checks')
            return
    else:
        # nothing to do
        log.info('AppArmor disabled')


def _apparmor_enabled():
    # checks sysfs if AA is enabled
    if os.path.exists('/sys/module/apparmor/parameters/enabled'):
        with open("/sys/module/apparmor/parameters/enabled") as file:
            if file.read().strip() == "Y":
                return True


def _apparmor_primitive_check():
    # check amount of files in /etc/apparmor.d/
    apparmor_files = Command.run(
        ['find', '/etc/apparmor.d/'], raise_on_error=False
    ).output
    if apparmor_files and apparmor_files.count('\n') > DEFAULT_ETC_FILE_COUNT:
        message = dedent('''\n
            Looks like customized AppArmor setup is in use:
            please install "apparmor-parser" as aa-status is
            needed to perform a proper check.
        ''')
        log.error(message)
        return True


def _apparmor_standard_profiles_modified():
    # verify AA files against rpm db
    profile_package = 'apparmor-profiles'
    if _find_modified_profiles(profile_package):
        message = dedent('''\n
            Modified AppArmor profiles found,
            please verify changes to the files from: "rpm -V {}".
        ''')
        log.error(message.format(profile_package))
        return True


def _apparmor_extended_profiles_modified():
    # check packages that carry AA profiles for in place modification
    for pkg in ADDITIONAL_AA_PROFILES:
        path_filter = '/etc/apparmor.d'
        if _find_modified_profiles(pkg, path_filter):
            message = dedent('''\n
                Modified AppArmor profiles found,
                please verify changes to profiles from "{}": "rpm -V {}".
            ''')
            log.error(message.format(path_filter, pkg))
            return True


def _find_modified_profiles(pkg, path_filter=None):
    modified_files = Command.run(
        ['rpm', '-V', pkg], raise_on_error=False
    ).output
    for line in modified_files.splitlines():
        if path_filter and line.find(path_filter) == -1:
            continue
        if (line[2] == "5"):
            return True


def _apparmor_additional_profiles(aa_data):
    # check amount of loaded AA profiles
    if len(aa_data["profiles"]) > DEFAULT_PROFILE_COUNT:
        return True
