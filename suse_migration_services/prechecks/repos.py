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
"""Module for checking repos that are not supported when migrating"""
import os
import configparser
import logging

from suse_migration_services.defaults import Defaults


def remote_repos(migration_system=False):
    """Function to check for repos that are not supported when migrating"""
    log = logging.getLogger(Defaults.get_migration_log_name())
    repos_path = '/etc/zypp/repos.d'
    if migration_system:
        repos_path = Defaults.get_system_root_path() + repos_path
    no_remote_repos = []

    if os.path.exists(repos_path):
        repos_list = os.listdir(repos_path)
        config = configparser.RawConfigParser()
        if not repos_list:
            log.error('No repositories in {}'.format(repos_path))
            return

        migration_accepted_prefixes = ('http', 'ftp', 'plugin:/susecloud')
        for repo in repos_list:
            repo_path = os.sep.join(
                [repos_path, repo]
            )
            config.read(repo_path)
            repo_section = dict(config)
            for section in repo_section.keys():
                repo_info = dict(config.items(section))
                if repo_info:
                    if not repo_info['baseurl'].startswith(migration_accepted_prefixes):
                        if repo_info['baseurl'] not in no_remote_repos:
                            no_remote_repos.append(repo_info['baseurl'])

    if no_remote_repos:
        zypper_cmd = 'zypper repos --url'
        log.warning(
            'The following repositories may cause the migration to fail, as they '
            'may not be available during the migration:\n%s\nPlease, check those '
            'before starting the migration\nTo see all the repositories and '
            'their urls, you can run "%s"\n',
            '\n'.join(no_remote_repos), zypper_cmd,
        )
