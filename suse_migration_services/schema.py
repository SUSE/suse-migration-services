schema = {
    'debug': {
        'required': False,
        'type': 'boolean'
    },
    'migration_product': {
        'required': False,
        'type': 'string'
    },
    'preserve': {
        'required': False,
        'type': 'dict',
        'schema': {
            'rules': {
                'required': False,
                'type': 'list',
                'nullable': False
            },
            'static': {
                'required': False,
                'type': 'list',
                'nullable': False
            },
        }
    },
    'soft_reboot': {
        'required': False,
        'type': 'boolean'
    },
    'use_zypper_migration': {
        'required': False,
        'type': 'boolean'
    },
    'verbose_migration': {
        'required': False,
        'type': 'boolean'
    },
    'build_host_independent_initrd': {
        'required': False,
        'type': 'boolean'
    },
    'pre_checks_fix': {
        'required': False,
        'type': 'boolean'
    }
}
