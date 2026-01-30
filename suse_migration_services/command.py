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
import logging
import os
import subprocess
from collections import namedtuple

# project
from suse_migration_services.defaults import Defaults
from suse_migration_services.exceptions import (
    DistMigrationCommandException,
    DistMigrationCommandNotFoundException,
)

log = logging.getLogger(Defaults.get_migration_log_name())


class Command:
    """
    **Implements command invocation**

    An instance of Command provides methods to invoke external
    commands in blocking and non blocking mode. Control of
    stdout and stderr is given to the caller
    """

    @staticmethod
    def run(command, custom_env=None, raise_on_error=True):
        """
        Execute a program and block the caller. The return value
        is a hash containing the stdout, stderr and return code
        information. Unless raise_on_error is set to false an
        exception is thrown if the command exits with an error
        code not equal to zero

        Example:

        .. code:: python

            result = Command.run(['ls', '-l'])

        :param list command: command and arguments
        :param list custom_env: custom os.environ
        :param bool raise_on_error: control error behaviour

        :return:
            Contains call results in command type

            .. code:: python

                command(output='string', error='string', returncode=int)

        :rtype: namedtuple
        """
        from .path import Path

        command_type = namedtuple('command', ['output', 'error', 'returncode'])
        environment = os.environ
        if custom_env:
            environment = custom_env
        if not Path.which(command[0], custom_env=environment, access_mode=os.X_OK):
            message = 'Command "%s" not found in the environment' % command[0]
            if not raise_on_error:
                return command_type(output=None, error=None, returncode=-1)
            else:
                log.error(message)
                raise DistMigrationCommandNotFoundException(message)
        try:
            log.info('Calling: {0}'.format(command))
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment
            )
        except Exception as issue:
            raise DistMigrationCommandException(
                '{0}: {1}: {2}'.format(command[0], type(issue).__name__, issue)
            )
        output, error = process.communicate()
        if process.returncode != 0 and not error:
            error = bytes(b'(no output on stderr)')
        if process.returncode != 0 and not output:
            output = bytes(b'(no output on stdout)')
        if process.returncode != 0 and raise_on_error:
            log.error(
                'EXEC: Failed with stderr: {0}, stdout: {1}'.format(error.decode(), output.decode())
            )
            raise DistMigrationCommandException(
                '{0}: stderr: {1}, stdout: {2}'.format(command[0], error.decode(), output.decode())
            )
        return command_type(
            output=output.decode(), error=error.decode(), returncode=process.returncode
        )
