#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import socket

import pika

from config import (
    host,
    password,
    port,
    queue,
    user,
    virtual_host,
)


PIKA_EXCEPTIONS = (
    pika.exceptions.AMQPConnectionError,
    pika.exceptions.ChannelClosed,
    pika.exceptions.ConnectionClosed,
    pika.exceptions.NoFreeChannels,
    socket.timeout
)


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


def build_pika_connection(host, port, virtual_host, user, password):
    return pika.BlockingConnection(
        pika.ConnectionParameters(
            host=host,
            port=port,
            virtual_host=virtual_host,
            connection_attempts=10,
            socket_timeout=10,
            retry_delay=1,
            credentials=pika.credentials.PlainCredentials(
                user,
                password
            )
        )
    )


def handler(event, context):
    connection = None
    try:
        connection = build_pika_connection(host, port, virtual_host, user, password)

        channel = connection.channel()
        channel.queue_declare(queue=queue)

        for record in event['Records']:
            # Skip anything that's not an S3 ObjectCreated:put event.
            if record['eventSource'] != 'aws:s3' or record['eventName'] != 'ObjectCreated:Put':
                continue

            # Extract crash id--if it's not a raw_crash object, skip it.
            crash_id = extract_crash_id(record)
            if crash_id is None:
                continue

            props = pika.BasicProperties(delivery_mode=2)
            channel.basic_publish(
                exchange='',
                routing_key=queue,
                body=crash_id,
                properties=props
            )

    except PIKA_EXCEPTIONS as pika_exc:
        # We've told the pika connection to retry a bunch, so if we hit this,
        # then evil is a foot and there isn't much we can do about it.
        print('Error: amqp publish failed: %s %s' % (crash_id, pika_exc))

    finally:
        if connection is not None:
            connection.close()
