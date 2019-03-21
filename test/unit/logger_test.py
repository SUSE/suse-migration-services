from unittest.mock import (
    patch, Mock
)
from pytest import raises
from collections import namedtuple
from suse_migration_services.defaults import Defaults
import logging

from suse_migration_services.logger import (
    LoggerSchedulerFilter,
    InfoFilter,
    DebugFilter,
    ErrorFilter,
    WarningFilter,
    log_init,
    log
)
from suse_migration_services.exceptions import (
    DistMigrationLoggingException
)


class TestLoggerSchedulerFilter(object):
    def setup(self):
        self.scheduler_filter = LoggerSchedulerFilter()

    def test_filter(self):
        MyRecord = namedtuple(
            'MyRecord',
            'name'
        )
        ignorables = [
            'apscheduler.scheduler',
            'apscheduler.executors.default'
        ]
        for ignorable in ignorables:
            record = MyRecord(name=ignorable)
            assert self.scheduler_filter.filter(record) is False


class TestInfoFilter(object):
    def setup(self):
        self.info_filter = InfoFilter()

    def test_filter(self):
        MyRecord = namedtuple(
            'MyRecord',
            'levelno'
        )
        record = MyRecord(levelno=logging.INFO)
        assert self.info_filter.filter(record) is True
        record = MyRecord(levelno=logging.ERROR)
        assert self.info_filter.filter(record) is None


class TestDebugFilter(object):
    def setup(self):
        self.debug_filter = DebugFilter()

    def test_filter(self):
        MyRecord = namedtuple(
            'MyRecord',
            'levelno'
        )
        record = MyRecord(levelno=logging.DEBUG)
        assert self.debug_filter.filter(record) is True
        record = MyRecord(levelno=logging.INFO)
        assert self.debug_filter.filter(record) is None


class TestErrorFilter(object):
    def setup(self):
        self.error_filter = ErrorFilter()

    def test_filter(self):
        MyRecord = namedtuple(
            'MyRecord',
            'levelno'
        )
        record = MyRecord(levelno=logging.ERROR)
        assert self.error_filter.filter(record) is True
        record = MyRecord(levelno=logging.WARNING)
        assert self.error_filter.filter(record) is None


class TestWarningFilter(object):
    def setup(self):
        self.warning_filter = WarningFilter()

    def test_filter(self):
        MyRecord = namedtuple(
            'MyRecord',
            'levelno'
        )
        record = MyRecord(levelno=logging.WARNING)
        assert self.warning_filter.filter(record) is True
        record = MyRecord(levelno=logging.ERROR)
        assert self.warning_filter.filter(record) is None


class TestLogger(object):
    def test_set_logfile_path_not_found(self):
        with raises(DistMigrationLoggingException):
            log.set_logfile(Defaults.get_migration_log_file())

    @patch('logging.FileHandler')
    def test_set_logfile(self, mock_file_handler):
        log.set_logfile('../data/logfile')
        mock_file_handler.assert_called_once_with(
            filename='../data/logfile', encoding='utf-8'
        )

    @patch('os.path.exists')
    @patch('logging.getLogger')
    def test_log_init(self, mock_get_logger, mock_os_path_exists):
        log = Mock()
        mock_os_path_exists.return_value = True
        mock_get_logger.return_value = log
        log_init()
        log.set_logfile.assert_called_once_with(
            '/system-root/var/log/distro_migration.log'
        )
