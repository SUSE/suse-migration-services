import logging

from suse_migration_services.command import Command
from suse_migration_services.defaults import Defaults
from suse_migration_services.fstab import Fstab
from suse_migration_services.logger import Logger


def encryption():
    Logger.setup(system_root=False)
    log = logging.getLogger(Defaults.get_migration_log_name())
    fstab = Fstab()
    fstab.read('/etc/fstab')
    fstab_entries = fstab.get_devices()

    for fstab_entry in fstab_entries:
        result = Command.run(
            ["blkid", "-s", "TYPE", "-o", "value", fstab_entry.device]
        )
        if result.returncode == 0:
            if 'LUKS' in result.output:
                log.warning(
                    'There are encrypted filesystems: {}, this may be an '
                    'issue when migrating'.format(fstab_entry.device)
                )
