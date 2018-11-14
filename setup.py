#!/usr/bin/env python
import platform

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from suse_migration_services.version import __VERSION__

python_version = platform.python_version().split('.')[0]

with open('.virtualenv.requirements.txt') as f:
    requirements = f.read().splitlines()

config = {
    'name': 'suse_migration_services',
    'description': 'SUSE Distribution Migration Services',
    'author': 'PubCloud Development team',
    'url': 'https://github.com/SUSE/suse-migration-services',
    'download_url': 'https://github.com/SUSE/suse-migration-services',
    'author_email': 'public-cloud-dev@susecloud.net',
    'version': __VERSION__,
    'install_requires': requirements,
    'packages': ['suse_migration_services'],
    'entry_points': {
        'console_scripts': [
            'suse-migration-mount-system=suse_migration_services.units.mount_system:main',
            'suse-migration-umount-system=suse_migration_services.units.umount_system:main',
            'suse-migration-setup-host-network=suse_migration_services.units.setup_host_network:main',
            'suse-migration-prepare=suse_migration_services.units.prepare:main',
            'suse-migration=suse_migration_services.units.migrate:main'
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
