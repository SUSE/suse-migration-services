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
"""Call prechecks for LSM migration (apparmor to selinux)"""
import logging
import json
import os
import subprocess

from typing import Optional

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
    manual_check_needed = False
    if migration_system:
        # only relevant on the system that is being migrated
        log.info('Skipped LSM migration checks.')
        return
    if _apparmor_enabled():
        try:
            aa_data = json.loads(subprocess.run(['aa-status', '--json'], stdout=subprocess.PIPE).stdout)
        except FileNotFoundError:
            log.warn("'aa-status' not available, in-depth checks not possible.")
            _apparmor_primitive_check()
            return
        if _apparmor_standard_profiles_modified():
            manual_check_needed = True
        if _apparmor_additional_profiles(aa_data):
            if _apparmor_extended_profiles_modified():
                manual_check_needed = True
            # look at loaded profiles
            if _apparmor_analyze_profiles(aa_data):
                # not possible ATM
                manual_check_needed = True
    else:
        # nothing to do
        log.info('AppArmor disabled')
    if manual_check_needed:
        log.error('Non-default AppArmor setup detected, please review the highlighted changes.')


def _apparmor_enabled():
    # checks sysfs if AA is enabled
    retval = False
    if os.path.exists('/sys/module/apparmor/parameters/enabled'):
        with open("/sys/module/apparmor/parameters/enabled", "r") as file:
            if file.read().strip() == "Y":
                retval = True
    return retval


def _apparmor_primitive_check():
    # check amount of files in /etc/apparmor.d/
    retval = False
    apparmor_files = subprocess.run(['find', '/etc/apparmor.d/'], stdout=subprocess.PIPE).stdout
    if apparmor_files.count(b"\n") > DEFAULT_ETC_FILE_COUNT:
        log.error("Looks like customized AppArmor setup is in use: please install 'apparmor-parser' as aa-status is needed to perform a proper check.")
        retval = True
    return retval


def _apparmor_standard_profiles_modified():
    # verify AA files against rpm db
    retval = False
    if __find_modified_profiles('apparmor-profiles'):
        log.error("Modified AppArmor profiles found, please verify changes to the files from: 'rpm -V {}'.".format('apparmor-profiles'))
        retval = True
    return retval


def _apparmor_extended_profiles_modified():
    # check packages that carry AA profiles for in place modification
    retval = False
    for pkg in ADDITIONAL_AA_PROFILES:
        path_filter = '/etc/apparmor.d'
        if __find_modified_profiles(pkg, path_filter):
            log.error("Modified AppArmor profiles found, please verify changes to profiles from '{}': 'rpm -V {}'.".format(path_filter, pkg))
            retval = True
    return retval


def __find_modified_profiles(pkg: str, path_filter: Optional[str] = None) -> bool:
    retval = False
    modified_files = subprocess.run(['rpm', '-V', pkg], stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace')
    for line in modified_files.splitlines():
        if path_filter and line.find(path_filter) == -1:
            continue
        if (line[2] == "5"):
            retval = True
    return retval


def _apparmor_additional_profiles(aa_data):
    # check amount of loaded AA profiles
    retval = False
    if len(aa_data["profiles"]) > DEFAULT_PROFILE_COUNT:
        retval = True
    return retval


def _apparmor_analyze_profiles(aa_data):
    # investigate loaded AA profiles closer
    # XXX: not aware of any profiles that can not be migrated
    #      mitigation should be logged as well
    retval = False
    if aa_data["profiles"].get("docker-default"):
        log.info("docker-default: {}".format(aa_data["profiles"].get("docker-default")))
        # docker is okay
        retval = False
    return retval
