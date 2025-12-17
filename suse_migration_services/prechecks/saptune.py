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
"""Module for checking sapconf/saptune configuration

Determines the state (enabled/disabled/not-found) of saptune and sapconf service and
predicts the migration outcome for SAP tuning (how saptune will be configured).
When called from the migration system the script writes a marker file
(/var/tmp/migration-saptune) for the saptune package to configure itself when
installed/upgraded.

If the migration prediction cannot be determined, a warning is printed and no
marker file is written.
An error (migration blocker) is only a misconfigured tuning (both sapconf
and saptune are enabled)."""


import os
import logging
from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults
from typing import List, Union


log = logging.getLogger(Defaults.get_migration_log_name())


def check_saptune(migration_system=False):
    """Checks sapconf and saptune service state (enabled/disabled/not-found), prints
    the migration prediction and writes the marker file for the saptune package
    scripts (only in the migration system)."""

    path_prefix = '/system-root' if migration_system else ''

    # Get OS.
    os = _get_os(path_prefix)
    if not os:
        log.warning('Could not determine OS!')
        return  # no migration hint

    # Get pattern.
    patterns = _get_installed_patterns(path_prefix)
    if not patterns:
        log.warning('Could not get installed patterns!')
        return  # no migration hint

    # Get enabled status of sapconf and saptune (enabled/disabled/not-found).
    sapconf_enabled_state = _get_service_enabled_state('sapconf.service', path_prefix=path_prefix)
    saptune_enabled_state = _get_service_enabled_state('saptune.service', path_prefix=path_prefix)

    # Build migration outcome lookup table.
    base_tuning_tuple = ('saptune will tune with the SAP_Base Solution', 'base')
    no_tuning_tuple = ('saptune will have no tuning configured', 'none')
    keep_tuning_tuple = ('saptune will continue with the current tuning', 'keep')
    not_installed_tuple = ('saptune will not be installed', None)
    if os == 'SLES':
        lookup = {'saptune:not-found sapconf:enabled': base_tuning_tuple,
                  'saptune:not-found sapconf:disabled': no_tuning_tuple}
        if 'sap-server' in patterns:
            lookup['saptune:not-found sapconf:not-found'] = base_tuning_tuple
        else:
            lookup['saptune:not-found sapconf:not-found'] = not_installed_tuple

    elif os == 'SLES_SAP':
        lookup = {'saptune:not-found sapconf:not-found': no_tuning_tuple,
                  'saptune:enabled sapconf:not-found': keep_tuning_tuple,
                  'saptune:disabled sapconf:not-found': no_tuning_tuple,
                  'saptune:not-found sapconf:enabled': base_tuning_tuple,
                  'saptune:enabled sapconf:enabled': base_tuning_tuple,
                  'saptune:disabled sapconf:enabled': base_tuning_tuple,
                  'saptune:not-found sapconf:disabled': no_tuning_tuple,
                  'saptune:enabled sapconf:disabled': keep_tuning_tuple,
                  'saptune:disabled sapconf:disabled': no_tuning_tuple}

    # Calculate migration outcome.
    current_state = f'saptune:{saptune_enabled_state} sapconf:{sapconf_enabled_state}'
    try:
        prediction, marker_content = lookup[current_state]
    except:  # noqa: E722
        log.warning(f'Unknown configuration "{current_state}"!')
        return  # no migration hint

    # Print infos.
    log.info(f'Installed SLE product: {os}')
    log.info(f'''Installed patterns: {', '.join(patterns)}''')
    log.info(f'sapconf.service: {sapconf_enabled_state}')
    log.info(f'saptune.service: {saptune_enabled_state}')
    if current_state == 'saptune:enabled sapconf:enabled':
        log.error('Both sapconf and saptune are enabled! This is a misconfiguration and should be resolved before migrating!')
    log.info(f'Migration outcome: {prediction}')
    if marker_content:
        log.info(f'Marker content: {marker_content}')

    # Write marker
    if migration_system and marker_content:
        if not _write_marker(marker_content, path_prefix=path_prefix):
            log.error('Could not write the marker file! Unpredictable migration outcome.')


def _get_os(path_prefix: str = '') -> Union[str, None]:
    """Returns product (SLES, SLES_SAP, None) by checking /etc/products.d/."""
    if os.path.exists(f'{path_prefix}/etc/products.d/SLES.prod'):
        return 'SLES'
    if os.path.exists(f'{path_prefix}/etc/products.d/SLES_SAP.prod'):
        return 'SLES_SAP'
    else:
        return None


def _get_installed_patterns(path_prefix: str = '') -> List[str]:
    """Returns list of installed patterns."""
    patterns = []
    cmd = ['zypper', '--root', path_prefix] if path_prefix else ['zypper']
    cmd.extend(['--terse', '--no-refresh', 'patterns', '-i'])
    for line in Command.run(cmd).output.split('\n'):
        if line.startswith('i'):
            try:
                patterns.append(line.split('|')[1].strip())
            except:  # noqa: E722
                pass  # don't care about errors...
    return patterns


def _get_service_enabled_state(service: str, path_prefix: str = '') -> str:
    """Returns if the systemd service is enabled, disabled or missing by checking
    the link in the default target wants directory."""
    if not os.path.exists(f'{path_prefix}/usr/lib/systemd/system/{service}'):
        return 'not-found'
    default_target = os.path.basename(os.path.realpath(f'{path_prefix}/etc/systemd/system/default.target'))
    service_link = f'{path_prefix}/etc/systemd/system/{default_target}.wants/{service}'
    return 'enabled' if os.path.lexists(service_link) else 'disabled'


def _write_marker(marker_content: str, path_prefix: str = '') -> bool:
    """Writes marker for saptune install helper."""
    try:
        with open(f'{path_prefix}/var/tmp/migration-saptune', 'w') as f:
            f.write(marker_content)
            return True
    except Exception as err:
        log.critical(f'Could not write migration marker. Tuning is not as expected after migration! Error: {err}')
        return False
