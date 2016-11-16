#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import pika

from config import host
from config import password
from config import port
from config import queue
from config import user
from config import virtual_host


def is_crash_id(crash_id):
    """Verifies a given string is a crash id

    :arg str crash_id: the string in question

    :returns: True if it's a crash id and False if not

    """
    return (
        # Verify length of the string
        len(crash_id) == 36 and

        # The 7-to-last character is either a 0 (ACCEPT) or a 1 (DEFER)
        crash_id[-7] in ('0', '1')
    )


def extract_crash_id(record):
    """Given a record, extracts the crash id

    :arg dict record: the AWS event record

    :returns: None (not a crash id) or the crash_id

    """
    try:
        key = record['s3']['object']['key']
        if not key.startswith('/v2/raw_crash/'):
            return None
        crash_id = key.rsplit('/', 1)[-1]
        if not is_crash_id(crash_id):
            return None
        return crash_id
    except (KeyError, IndexError):
        return None


def handler(event, context):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=host,
            port=port,
            virtual_host=virtual_host,
            connection_attempts=10,
            socket_timeout=10,
            retry_delay=1,
            credentials=pika.credentials.PlainCredentials(
                user,
                password,
            )
        )
    )

    try:
        channel = connection.channel()
        channel.queue_declare(queue=queue)
        # FIXME not sure if this is still needed
        # makes messages permanent
        # basic_properties = pika.BasicProperties(delivery_mode=3)

        for record in event['Records']:
            # Skip anything that's not an S3 ObjectCreated:put event.
            if record['eventSource'] != 'aws:s3' or record['eventName'] != 'ObjectCreated:Put':
                continue

            # Extract crash id--if it's not a raw_crash object, skip it.
            crash_id = extract_crash_id(record)
            if crash_id is None:
                continue

            try:
                channel.basic_publish(
                    exchange='',
                    routing_key=queue,
                    body=crash_id,
                    # properties=basic_properties,
                )
            except Exception:
                print('Error: amqp publish failed: ' + json.dumps(crash_id))

    finally:
        connection.close()
