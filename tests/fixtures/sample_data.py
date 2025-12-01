"""
Sample data for tests
"""

# Sample network interface data
SAMPLE_INTERFACES = {
    'eth0': {
        'addr': '192.168.1.100',
        'netmask': '255.255.255.0',
        'mac': '00:11:22:33:44:55',
    },
    'wlan0': {
        'addr': '10.0.0.50',
        'netmask': '255.255.0.0',
        'mac': 'AA:BB:CC:DD:EE:FF',
    },
}

# Sample HTTP responses
SAMPLE_HTTP_RESPONSE = {
    'status': 'ok',
    'data': {
        'message': 'Success',
        'items': [1, 2, 3],
    },
}

SAMPLE_ERROR_RESPONSE = {
    'error': {
        'code': 400,
        'message': 'Bad Request',
    },
}

# Sample strings for slugify tests
SLUGIFY_TEST_CASES = [
    ('Hello World', 'hello-world'),
    ('Test_String-123', 'test-string-123'),
    ('CamelCaseString', 'camelcasestring'),
    ('String with   spaces', 'string-with-spaces'),
]

# Sample boolean conversion test cases
BOOL_TEST_CASES = [
    ('true', True),
    ('True', True),
    ('TRUE', True),
    ('yes', True),
    ('Yes', True),
    ('y', True),
    ('1', True),
    ('on', True),
    ('false', False),
    ('False', False),
    ('FALSE', False),
    ('no', False),
    ('No', False),
    ('n', False),
    ('0', False),
    ('off', False),
    ('invalid', None),  # Should return default
]
