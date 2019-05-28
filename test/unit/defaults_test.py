from suse_migration_services.defaults import Defaults


class TestDefaults(object):
    def setup(self):
        self.defaults = Defaults()

    def test_get_migration_config_file(self):
        assert self.defaults.get_migration_config_file() == \
            '/etc/migration-config.yml'
