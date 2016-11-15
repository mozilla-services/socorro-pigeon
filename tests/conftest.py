# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import imp
import parser
import os
import sys

from lambda_local import context
import pytest


CONFIG_MODULE = """
import os

host = os.environ['RABBITMQ_HOST']
port = int(os.environ['RABBITMQ_PORT'])
user = os.environ['RABBITMQ_USER']
password = os.environ['RABBITMQ_PASS']
virtual_host = os.environ['RABBITMQ_VHOST']
queue = os.environ['RABBITMQ_QUEUE']
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
        ctx = context.Context(
            timeout=3,
            arn_string='',
            version_name=''
        )
        result = handler(events, ctx.activate())
        return result


@pytest.fixture
def client():
    """Returns an AWS Lambda mock that runs pigeon thing"""
    return PigeonClient()
