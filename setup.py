#!/usr/bin/env python
import platform

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from suse_migration_services.version import __VERSION__

python_version = platform.python_version().split('.')[0]

config = {
    'name': 'suse_migration_services',
    'description': 'SUSE Distribution Migration Services',
    'author': 'PubCloud Development team',
    'url': 'https://github.com/SUSE/suse-migration-services',
    'download_url': 'https://github.com/SUSE/suse-migration-services',
    'author_email': 'public-cloud-dev@susecloud.net',
    'version': __VERSION__,
    'install_requires': ['setuptools', 'PyYAML', 'cerberus'],
    'packages': ['suse_migration_services'],
    'entry_points': {
        'console_scripts': [
            'suse-migration-mount-system=suse_migration_services.units.mount_system:main',
            'suse-migration-ssh-keys=suse_migration_services.units.ssh_keys:main',
            'suse-migration-setup-host-network=suse_migration_services.units.setup_host_network:main',
            'suse-migration-prepare=suse_migration_services.units.prepare:main',
            'suse-migration=suse_migration_services.units.migrate:main',
            'suse-migration-apparmor-selinux=suse_migration_services.units.apparmor_migration:main',
            'suse-migration-wicked-networkmanager=suse_migration_services.units.wicked_migration:main',
            'suse-migration-grub-setup=suse_migration_services.units.grub_setup:main',
            'suse-migration-update-bootloader=suse_migration_services.units.update_bootloader:main',
            'suse-migration-regenerate-initrd=suse_migration_services.units.regenerate_initrd:main',
            'suse-migration-kernel-load=suse_migration_services.units.kernel_load:main',
            'suse-migration-reboot=suse_migration_services.units.reboot:main',
            'suse-migration-product-setup=suse_migration_services.units.product_setup:main',
            'suse-migration-post-mount-system=suse_migration_services.units.post_mount_system:main',
            # Not installed in units as it is installed as part of the suse-migration-pre-checks
            'suse-migration-pre-checks=suse_migration_services.prechecks.pre_checks:main'
        ]
    },
    'include_package_data': True,
    'license': 'GPLv3',
    'zip_safe': False,
    'classifiers': [
        # http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Operating System'
    ]
}

setup(**config)
