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
from typing import List

# project
from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults
from suse_migration_services.exceptions import (
    DistMigrationZypperException
)


class Zypper:
    """
    **Implements zypper invocation**
    """
    @staticmethod
    def run(args: List[str], raise_on_error=True, chroot=''):
        """
        Invoke zypper and block the caller. The return value is a
        ZypperCall instance containing the result of invocation.

        raise_on_error:
            is directly passed to the underlying Command.run invocation
            and thus will raise whenever zypper exists with a non-zero
            status. To check the status according to zypper sematics,
            use raise_on_error=False with ZypperCall.success and
            ZypperCall.raise_if_failed.

        chroot:
            run zypper chrooted against the given path
        """
        log_file = Defaults.get_migration_log_file(
            system_root=False if chroot else True
        )
        command_string = ' '.join(['zypper'] + list(args) + ['&>>', log_file])
        command = []
        if chroot:
            # Calling zypper in a new system root should be done in
            # offline systemd mode to prevent package scripts to access
            # services not necessarily present
            custom_env = {}
            custom_env['SYSTEMD_OFFLINE'] = '1'
            os.environ.update(custom_env)

            command += ['chroot', chroot]
        try:
            result = Command.run(
                command + ['bash', '-c', command_string],
                raise_on_error=raise_on_error
            )
        except Exception as issue:
            raise DistMigrationZypperException(
                'zypper failed with: {}'.format(issue)
            )
        return ZypperCall(args, command_string, result)


class ZypperCall:
    def __init__(self, args: List[str], command, result):
        self.args = args
        self.command = command
        self.output = result.output
        self.error = result.error
        self.returncode = result.returncode

    @property
    def success(self):
        """
        Evaluate the return code of zypper call

        In zypper any return code == 0 or >= 100 is considered success.
        Any return code different from 0 and < 100 is treated as an
        error we care for. Return codes >= 100 indicates an issue
        like 'new kernel needs reboot of the system' or similar which
        we don't care in the scope of image building

        :return: True|False

        :rtype: boolean
        """
        error_codes = [
            104,  # ZYPPER_EXIT_INF_CAP_NOT_FOUND
            105,  # ZYPPER_EXIT_ON_SIGNAL
            106,  # ZYPPER_EXIT_INF_REPOS_SKIPPED
        ]

        if self.returncode == 0:
            # All is good
            return True
        elif self.returncode in error_codes:
            return False
        elif self.returncode >= 100:
            # Treat all other 100 codes as non error codes
            return True

        # Treat any other error code as error
        return False

    def raise_if_failed(self):
        """
        Raise `DistMigationZypperException` if zypper exited unsuccessfully.
        """
        if self.success:
            return

        raise DistMigrationZypperException(
            '{0}: failed with: {1}: {2}'.format(
                self.command, self.output, self.error
            )
        )

    def log_if_failed(self, log):
        """
        log output and error when failed
        """
        if not self.success:
            log.error(
                '{0}: failed with: {1}: {2}'.format(
                    self.command, self.output, self.error
                )
            )
