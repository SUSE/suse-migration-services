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
"""Call prechecks for HA provided by crmsh"""
import logging
import os
import subprocess
import shutil

from suse_migration_services.defaults import Defaults


log = logging.getLogger(Defaults.get_migration_log_name())


def check_wicked2nm(migration_system=False):
    wicked_config_path = '/var/cache/wicked_config'
    if migration_system:
        wicked_config_path = os.sep.join([Defaults.get_system_root_path(), wicked_config_path])
    if not os.access(os.sep.join([wicked_config_path, 'config.xml']), os.F_OK):
        if not shutil.which('wicked2nm') or not shutil.which('wicked'):
            log.info('No wicked setup available. Skipping wicked2nm check.')
            return
        log.info('Checking wicked config present on live system')
        wicked_config_output = subprocess.Popen(['wicked', 'show-config'], stdout=subprocess.PIPE)
        try:
            subprocess.check_output(
                ['wicked2nm', 'migrate', '--dry-run', '-'],
                stdin=wicked_config_output.stdout,
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as e:
            log.error('Wicked to NetworkManager migration pre-check failed:{0}{1}'.format(
                os.linesep, e.output.decode('utf-8')
            ))
            return False
    else:
        log.info('Checking copied wicked config at: ' + wicked_config_path)
        try:
            subprocess.check_output(
                [
                    'wicked2nm', 'migrate', '--dry-run',
                    '--netconfig-path', os.sep.join([wicked_config_path, 'config']),
                    '--netconfig-dhcp-path', os.sep.join([wicked_config_path, 'dhcp']),
                    os.sep.join([wicked_config_path, 'config.xml'])
                ],
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as e:
            log.error('Wicked to NetworkManager migration pre-check failed:{0}{1}'.format(
                os.linesep, e.output.decode('utf-8')
            ))
            return False
