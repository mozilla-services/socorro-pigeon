# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import imp
import parser
import os
import sys
import uuid

import pytest


CONFIG_MODULE = """
import os

# These have to match the rabbitmq container
user = os.environ['RABBITMQ_DEFAULT_USER']
password = os.environ['RABBITMQ_DEFAULT_PASS']
virtual_host = os.environ['RABBITMQ_DEFAULT_VHOST']

host = os.environ['RABBITMQ_HOST']
port = 5672
queue = 'antennadev.normal'
"""


def build_config_module():
    """Generate a config module and insert it

    pigeon requires a config.py file which has the configuration in it. We need
    one for tests, but that's kind of irritating. So we fake a module and stick
    it in sys.modules.
    """
    st = parser.suite(CONFIG_MODULE)
    code = st.compile('config.py')
    cfg = imp.new_module('config')
    exec(code, cfg.__dict__)
    return cfg

sys.modules['config'] = build_config_module()

# Insert the repository root into sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pigeon import handler  # noqa


def crash_id_to_path(crash_id):
    return '/v2/raw_crash/{entropy}/{date}/{crashid}'.format(
        entropy=crash_id[0:3],
        date='20' + crash_id[-6:],
        crashid=crash_id
    )


class LambdaContext:
    """Context class that mimics the AWS Lambda context

    http://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    """
    def __init__(self):
        self.aws_request_id = uuid.uuid4().hex

        self.log_group_name = '/aws/lambda/test'
        self.log_stream_name = '2016-11-15blahblah'

        self.function_name = 'test'
        self.memory_limit_in_mb = '384'
        self.function_version = '1'
        self.invoked_function_arn = 'arn:aws:lambda:us-west-2:blahblah:function:test'

        # FIXME(willkg): Keeping these as None until we need them.
        self.client_context = None
        self.identity = None

    def get_remaining_time_in_millis(self):
        # FIXME(willkg): Implement this when we need it
        return 5000


class PigeonClient:
    """Class for pigeon in the AWS lambda environment"""
    def build_crash_save_events(self, crash_ids):
        # FIXME(willkg): This only generates a record that has the stuff that
        # pigeon is looking for. It's not a full record.
        return {
            'Records': [
                {
                    'eventName': 'ObjectCreated:Put',
                    's3': {
                        'object': {
                            'key': crash_id_to_path(crash_id)
                        }
                    }
                }
                for crash_id in crash_ids
            ]
        }

    def run(self, events):
        result = handler(events, LambdaContext())
        return result


@pytest.fixture
def client():
    """Returns an AWS Lambda mock that runs pigeon thing"""
    return PigeonClient()
