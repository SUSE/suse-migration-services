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
import sys

# project
from suse_migration_services.exceptions import (
    DistMigrationLoggingException
)


class LoggerSchedulerFilter(logging.Filter):
    """Extended standard logging Filter."""

    def filter(self, record):
        """
        Messages from apscheduler scheduler instances are filtered out.

        They conflict with console progress information
        :param tuple record: logging message record
        :return: record.name
        :rtype: str
        """
        ignorables = [
            'apscheduler.scheduler',
            'apscheduler.executors.default'
        ]
        return record.name not in ignorables


class InfoFilter(logging.Filter):
    """Extended standard logging Filter."""

    def filter(self, record):
        """
        Only messages with record level INFO can pass.

        For messages with another level an extra handler is used
        :param tuple record: logging message record
        :return: record.name
        :rtype: str
        """
        if record.levelno == logging.INFO:
            return True


class DebugFilter(logging.Filter):
    """Extended standard debug logging Filter."""

    def filter(self, record):
        """
        Only messages with record level DEBUG can pass.

        For messages with another level an extra handler is used
        :param tuple record: logging message record
        :return: record.name
        :rtype: str
        """
        if record.levelno == logging.DEBUG:
            return True


class ErrorFilter(logging.Filter):
    """Extended standard error logging Filter."""

    def filter(self, record):
        """
        Only messages with record level ERROR can pass.

        For messages with another level an extra handler is used
        :param tuple record: logging message record
        :return: record.name
        :rtype: str
        """
        if record.levelno == logging.ERROR:
            return True


class WarningFilter(logging.Filter):
    """Extended standard warning logging Filter."""

    def filter(self, record):
        """
        Only messages with record level WARNING can pass.

        For messages with another level an extra handler is used
        :param tuple record: logging message record
        :return: record.name
        :rtype: str
        """
        if record.levelno == logging.WARNING:
            return True


class Logger(logging.Logger):
    """
    Extended logging facility based on Python logging.

    :param string name: name of the logger
    """

    def __init__(self, name):
        logging.Logger.__init__(self, name)
        self.message_format = '[%(levelname)-8s]: %(asctime)-8s | %(message)s'
        self.console_handlers = {}
        self._add_stream_handler(
            'info',
            self.message_format,
            [InfoFilter(), LoggerSchedulerFilter()]
        )
        # log WARNING messages to stdout
        self._add_stream_handler(
            'warning',
            self.message_format,
            [WarningFilter()]
        )
        # log DEBUG messages to stdout
        self._add_stream_handler(
            'debug',
            self.message_format,
            [DebugFilter()]
        )
        # log ERROR messages to stderr
        self._add_stream_handler(
            'error',
            self.message_format,
            [ErrorFilter()],
            sys.__stderr__
        )

    def _add_stream_handler(
        self, handler_type, message_format, message_filter,
        channel=sys.__stdout__
    ):
        handler = logging.StreamHandler(channel)
        handler.setFormatter(
            logging.Formatter(message_format, '%H:%M:%S')
        )
        for rule in message_filter:
            handler.addFilter(rule)
        self.addHandler(handler)
        self.console_handlers[handler_type] = handler

    def set_logfile(self, filename):
        """
        Set logfile handler.

        :param string filename: logfile file path
        """
        try:
            print(filename)
            logfile = logging.FileHandler(
                filename=filename, encoding='utf-8'
            )
            logfile.setFormatter(
                logging.Formatter(
                    self.message_format, '%H:%M:%S'
                )
            )
            logfile.addFilter(LoggerSchedulerFilter())
            self.addHandler(logfile)
        except Exception as issue:
            raise DistMigrationLoggingException(
                'Unable to set logging file {0} with'
                '{1}'.format(filename, issue))


logging.setLoggerClass(Logger)
log = logging.getLogger("suse-migration")
log.setLevel(logging.DEBUG)
