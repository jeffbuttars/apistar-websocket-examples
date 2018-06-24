#!/usr/bin/env python
# encoding: utf-8

import logging
import json
import random
import uuid
import argparse
import asyncio
import aiohttp

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

url_base = 'http://localhost:8000'


async def hello(ws):
    msg = await ws.receive_str()
    logger.info("%s", msg)


async def ping(ws):
    num = 1000
    logger.debug("Sending %s pings...", num)
    for _ in range(num):
        await ws.send_str('ping')
        pong = await ws.receive_str()
        if pong != 'pong':
            raise Exception("Not a pong: %s" % pong)

    logger.debug("Got %s pongs", num)


async def consumer(ws):
    num = 1000
    logger.debug("Sending %s random numbers", num)
    for _ in range(num):
        await ws.send_str('%s' % random.randint(0, 10000000))

    logger.debug("Sent %s numbers", num)


async def json_consumer(ws):
    num = 1000
    logger.debug("Sending %s random json message", num)
    for _ in range(num):
        await ws.send_json({
            'int': random.randint(0, 1000000),
            'uuid1': str(uuid.uuid1()),
            'uuid3': str(uuid.uuid3(uuid.NAMESPACE_DNS, 'apistar websockets')),
            'uuid4': str(uuid.uuid4()),
            'uuid5': str(uuid.uuid5(uuid.NAMESPACE_URL, 'apistar websockets')),
        })

    logger.debug("Sent %s json messages", num)


async def producer(ws):
    num = 1000
    logger.debug("Receiving %s random numbers", num)
    for _ in range(num):
        msg = await ws.receive_str()
        logger.debug("Received: %s", msg)

    logger.debug("Received %s numbers", num)


async def json_producer(ws):
    num = 1000
    logger.debug("Receiving %s json messages", num)
    for _ in range(num):
        msg = json.loads(await ws.receive_bytes())
        logger.debug("Received: %s", msg)

    logger.debug("Received %s json messages", num)


async def time(ws):
    num = 10
    logger.debug("Receiving %s time messages", num)
    for _ in range(num):
        msg = await ws.receive_str()
        logger.debug("Received: %s", msg)

    logger.debug("Received %s time messages", num)


async def sub(ws):
    num = 10
    logger.debug("Receiving %s subscription messages", num)
    for _ in range(num):
        msg = await ws.receive_str()
        logger.debug("Received: %s", msg)

    logger.debug("Received %s subscription messages", num)


async def crypto(ws):
    num = 10
    logger.debug("Receiving %s crypto price messages for", num)
    for _ in range(num):
        msg = json.loads(await ws.receive_bytes())
        logger.debug("Received: %s", msg)

    logger.debug("Received %s crypto messages", num)


async def crypto_managed(ws):
    num = 10
    logger.debug("Receiving %s crypto price messages for", num)
    for _ in range(num):
        msg = json.loads(await ws.receive_bytes())
        logger.debug("Received: %s", msg)

    logger.debug("Received %s crypto messages", num)


urls = {
    'hello': {
        'url': '/',
        'help': 'Return a hello and disconnects',
        'func': hello,
    },
    'ping': {
        'url': '/ping_pong',
        'help': 'Sends a ping and expects a pong.',
        'func': ping,
    },
    'consumer': {
        'url': '/consumer',
        'help': 'An all consuming black hole endpoint',
        'func': consumer,
    },
    'json_consumer': {
        'url': '/consumer/of/json',
        'help': 'An all json consuming black hole endpoint',
        'func': json_consumer,
    },
    'producer': {
        'url': '/producer',
        'help': 'Return random data forever',
        'func': producer,
    },
    'json_producer': {
        'url': '/producer/of/json',
        'help': 'Return random json data forever',
        'func': json_producer,
    },
    'time': {
        'url': '/timer',
        'help': 'Return the time about every second',
        'func': time,
    },
    'sub': {
        'url': '/search/subscribe/{topic}',
        'help': 'Subscribe to an information stream about "topic"',
        'arg': 'topic',
        'func': sub,
    },
    'crypto': {
        'url': '/crypto/price/{sym}',
        'help': 'Subscribe to price data about the crypto asset symbol of "sym"',
        'arg': 'sym',
        'func': crypto,
    },
    'crypto_managed': {
        'url': '/crypto/price/managed/{sym}',
        'arg': 'sym',
        'help': 'Subscribe to price data, on a managed endpoint, about the crypto asset symbol of "sym"',
        'func': crypto_managed,
    },
}

parser = argparse.ArgumentParser(description='Exercise WebSocket examples')
subparsers = parser.add_subparsers(help='subcommand help')

# Add sub commands for each endpoint
for cmd, obj in urls.items():
    p = subparsers.add_parser(cmd, help=obj.get('help', ''))
    p.add_argument('--url', default=obj.get('url'))
    if obj.get('arg'):
        p.add_argument(obj.get('arg'))

    p.set_defaults(func=obj.get('func'), argname=obj.get('arg', ''))


async def run(args):
    logger.debug("Running: %s", args)
    session = aiohttp.ClientSession()

    url = url_base + args.url
    if args.argname:
        kwargs = {args.argname: getattr(args, args.argname)}
        #  logger.debug("kwargs: %s", kwargs)
        url = url.format(**kwargs)

    logger.debug("Connecting to URL: %s", url)

    async with session.ws_connect(url) as ws:
        await args.func(ws)
        if not ws.closed:
            logger.debug("Closing connection...")
            await ws.close()

    logger.debug("Closing session...")
    await session.close()
    logger.debug("done")


def main():
    args = parser.parse_args()

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run(args))
        # Add a small bump to allow connections to clean up
        loop.run_until_complete(asyncio.sleep(0))
        loop.close()
    except KeyboardInterrupt:
        logger.debug("Keyboard Interrupt")
        loop.close()


if __name__ == '__main__':
    main()
