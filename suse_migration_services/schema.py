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
                'required': True,
                'type': 'list',
                'nullable': False
            }
        }
    },
    'soft_reboot': {
        'required': False,
        'type': 'boolean'
    },
    'use_zypper_migration': {
        'required': False,
        'type': 'boolean'
    }
}
