#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import socket
import time

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

# These values match Antenna throttling return values
ACCEPT = '0'
DEFER = '1'

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def statsd_incr(key, val=1):
    """Sends a specially formatted line for datadog to pick up for statsd incr"""
    print('MONITORING|%(timestamp)s|%(val)s|count|%(key)s|' % {
        'timestamp': int(time.time()),
        'key': key,
        'val': val
    })


def is_crash_id(crash_id):
    """Verifies a given string is a crash id

    :arg str crash_id: the string in question

    :returns: True if it's a crash id and False if not

    """
    return (
        # Verify length of the string
        len(crash_id) == 36 and

        # The 7-to-last character is a throttle result
        crash_id[-7] in (ACCEPT, DEFER)
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


def get_throttle_result(crash_id):
    return crash_id[-7]


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

    accepted_records = []

    for record in event['Records']:
        # Skip anything that's not an S3 ObjectCreated:put event.
        if record['eventSource'] != 'aws:s3' or record['eventName'] != 'ObjectCreated:Put':
            continue

        # Extract crash id--if it's not a raw_crash object, skip it.
        crash_id = extract_crash_id(record)
        logger.info('crash id: %s', crash_id)
        if crash_id is None:
            continue

        # Skip crashes that aren't marked for processing
        if get_throttle_result(crash_id) == DEFER:
            statsd_incr('antenna.pigeon.defer', 1)
            continue

        accepted_records.append(crash_id)

    if not accepted_records:
        return

    try:
        connection = build_pika_connection(host, port, virtual_host, user, password)
        props = pika.BasicProperties(delivery_mode=2)

        channel = connection.channel()
        channel.queue_declare(queue=queue)

        for crash_id in accepted_records:
            statsd_incr('antenna.pigeon.accept', 1)

            channel.basic_publish(
                exchange='',
                routing_key=queue,
                body=crash_id,
                properties=props
            )

    except PIKA_EXCEPTIONS:
        # We've told the pika connection to retry a bunch, so if we hit this,
        # then evil is a foot and there isn't much we can do about it.
        statsd_incr('antenna.pigeon.pika_error', 1)
        logger.exception('Error: amqp publish failed: %s', crash_id)

    finally:
        if connection is not None:
            connection.close()
