#!/usr/bin/env python3
import sys
from suse_migration_services.version import __VERSION__

level = sys.argv[1]

(major, minor, patch) = __VERSION__.split('.')

if level == 'patch':
    patch = int(patch) + 1
elif level == 'minor':
    minor = int(minor) + 1
elif level == 'major':
    major = int(major) + 1

print(f'{major}.{minor}.{patch}')
