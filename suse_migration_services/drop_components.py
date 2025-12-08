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
import os
import shutil
import pathlib
import logging
from tempfile import NamedTemporaryFile
from datetime import datetime

# project
from suse_migration_services.path import Path
from suse_migration_services.zypper import Zypper
from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults

log = logging.getLogger(Defaults.get_migration_log_name())


class DropComponents:
    """
    **Base class to drop packages, files from the system**

    When replacing an implementation for a certain feature
    with another implementation where the replacing implementation
    has no compatibility it may occur that the transition path
    contains steps that cannot be handled in the replacing RPM
    package or the to be replaced RPM or the combination thereof.

    In these cases an instance of DropComponents can be used to
    interfere in the upgrade process, rather than just driving
    the upgrade process.
    """
    def __init__(self):
        self.drop_packages = []
        self.drop_files_and_directories = []
        self.root_path = Defaults.get_system_root_path()
        self.backup_data = NamedTemporaryFile()
        self.backup_path = os.path.normpath(
            os.sep.join(
                [
                    self.root_path,
                    Defaults.get_migration_backup_path(),
                    datetime.now().strftime('%Y-%m-%d')
                ]
            )
        )

    def drop_package(self, name):
        self.drop_packages.append(name)

    def package_installed(self, name):
        package_call = Command.run(
            ['chroot', self.root_path, 'rpm', '-q', name],
            raise_on_error=False
        )
        if package_call.returncode == 0:
            return True
        return False

    def drop_path(self, path):
        if self.root_path:
            target_path = os.path.normpath(
                os.sep.join([self.root_path, path])
            )
            with open(self.backup_data.name, 'a') as backup:
                backup.write('{}{}'.format(target_path, os.linesep))

            self.drop_files_and_directories.append(target_path)

    def drop_perform(self):
        self._uninstall_packages()
        self._delete_paths()

    def _uninstall_packages(self):
        if self.drop_packages and self.root_path:
            zypper_call = Zypper.run(
                [
                    '--no-cd',
                    '--non-interactive',
                    '--gpg-auto-import-keys',
                    '--root', self.root_path,
                    'remove',
                    '--clean-deps'
                ] + self.drop_packages, raise_on_error=False
            )
            zypper_call.raise_if_failed()

    def _delete_paths(self):
        if self.drop_files_and_directories:
            Path.create(self.backup_path)
            Command.run(
                [
                    'rsync', '-avr', '--ignore-missing-args',
                    '--files-from', self.backup_data.name,
                    self.root_path,
                    '{}/'.format(self.backup_path)
                ]
            )
            for element in self.drop_files_and_directories:
                if os.path.isdir(element):
                    shutil.rmtree(element)
                else:
                    pathlib.Path(element).unlink(missing_ok=True)
