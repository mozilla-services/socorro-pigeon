#!/usr/bin/env python

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
                except Exception:
                    print('Error: invalid record: ' + json.dumps(record)
                    print(msg)
                    raise
                try:
                    channel.basic_publish(
                        exchange='',
                        routing_key=queue,
                        body=crash_id,
                        # properties=basic_properties,
                    )
                except Exception:
                    print('Error: amqp publish failed: ' + json.dumps(crash_id)
    finally:
        connection.close()
