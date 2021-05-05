# Copyright (c) 2021 SUSE Linux LLC.  All rights reserved.
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
import configparser

# project
from suse_migration_services.fstab import Fstab
from suse_migration_services.command import Command


def check_remote_repos():
    repos_path = '/etc/zypp/repos.d'
    no_remote_repos = []
    print("PEPE")
    if os.path.exists(repos_path):
        repos_list = os.listdir(repos_path)
        config = configparser.RawConfigParser()
        if not repos_list:
            print('No repositories in {}'.format(repos_path))
            return

        for repo in repos_list:
            repo_path = os.sep.join(
                [repos_path, repo]
            )
            print(repo_path)
            config.read(repo_path)
            repo_section = dict(config)
            print(repo_section)
            for section in repo_section.keys():
                repo_info = dict(config.items(section))
                if repo_info:
                    if not repo_info['baseurl'].startswith('http') and not repo_info['baseurl'].startswith('ftp'):
                        if repo_info['baseurl'] not in no_remote_repos:
                            no_remote_repos.append(repo_info['baseurl'])

    if no_remote_repos:
        print(
            'These repositories locations may be an issue when migrating: "{}". '
            'Please check before migration starts'.format(','.join(no_remote_repos)))


def check_fs_encryption():
    fstab = Fstab()
    fstab.read('/etc/fstab')
    fstab_entries = fstab.get_devices()

    for fstab_entry in fstab_entries:
        result = Command.run(
            ["blkid", "-s", "TYPE", "-o", "value", fstab_entry.device]
        )
        if result.returncode == 0:
            if 'LUKS' in result.output:
                print(
                    'There are encrypted filesystems: {}, this may be an '
                    'issue when migrating'.format(fstab_entry.device)
                )


def main():
    """
    DistMigration pre checks before migration starts

    Checks whether
      - repositories' locations are not remote
      - filesystems in fstab are using LUKS encryption
    """
    check_remote_repos()
    check_fs_encryption()
