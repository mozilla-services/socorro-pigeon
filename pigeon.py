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
            if record['eventName'] == 'ObjectCreated:Put':
                try:
                    key = record['s3']['object']['key']
                    crash_id = key.rsplit('/', 1)[-1]
                except Exception as exc:
                    print('Error: invalid record: ' + json.dumps(record))
                    print(exc)
                    raise
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
