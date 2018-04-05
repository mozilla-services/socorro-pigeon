#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Consumes and prints items from RabbitMQ queues.
#
# Note: Run this in the test container which has access to RabbitMQ.
#
# Usage: ./bin/consume_queue.py

import logging
import os
import sys


# Insert build/ directory in sys.path so we can import pika
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'build'
    )
)

# Kill logging so we don't have to listen to Pigeon logging
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger().disabled = True
logging.getLogger('pigeon').disabled = True


from pigeon import build_pika_connection, CONFIG  # noqa


def get_items(channel, queue):
    items = []
    method_frame, header_frame, body = channel.basic_get(queue=queue)
    while method_frame:
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        items.append(body.decode('ascii'))
        method_frame, header_frame, body = channel.basic_get(queue=queue)
    return items


if __name__ == '__main__':
    # Build a connection
    conn = build_pika_connection(
        CONFIG.host,
        CONFIG.port,
        CONFIG.virtual_host,
        CONFIG.user,
        CONFIG.password
    )
    channel = conn.channel()

    # Go through queues and consume and print contents
    for throttle, queue in CONFIG.queues:
        # Get all the items from the queue and print them out
        items = get_items(channel, queue)
        if not items:
            print('%s: No items' % queue)

        else:
            print('%s: %d items' % (queue, len(items)))
            for item in items:
                print('item: %s' % item)
