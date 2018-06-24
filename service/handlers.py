import asyncio
import aiohttp
import datetime
import random
import uuid
import logging

from apistar import Route
from apistar.websocket import status, WebSocket, WebSocketRequest
from apistar.exceptions import WebSocketDisconnect

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


TOPICS = ('games', 'puzzles', 'vacations', 'programs', 'jobs', 'python', 'apistar')
CRYPTO_URL = 'https://min-api.cryptocompare.com/data/price?fsym={fsym}&tsyms=USD,EUR'


# Very basic, connect with the client, send them 'Hello World!' then close the connection.
# The WebSocket connection will be automatically closed with a a code of 1000 if a
# WebSocket handler returns with an open socket.
async def hello(ws: WebSocket):
    await ws.connect()
    await ws.send('Hello World!')


# For as long as the client sends a 'ping', we'll send a pong.
# If the client doesn't send a 'ping', we close with a WebSocket error code
# If the client disconnects, we finish by simply returning from the handler
async def ping_pong(ws: WebSocket):
    await ws.connect()

    while True:
        # If you want know when the client disconnects, just catch it.
        try:
            ping = await ws.receive()

            if ping != 'ping':
                logger.error("Client didn't send a 'ping', sent '%s' instead", ping)
                ws.close(code=status.WS_1002_PROT_ERROR)
                return

            await ws.send('pong')
        except WebSocketDisconnect:
            logger.debug("Ping client disconnected")
            # Client disconnected, we're done
            return


# Simply accepts all incoming data until the client
# closes the connection.
async def consumer(ws: WebSocket):
    await ws.connect()

    while True:
        data = await ws.receive()
        logger.debug("consumer received: %s", data)
        # Do something with the data
        # ....


# Simply accepts all incoming json data until the client
# closes.
async def consumer_of_json(ws: WebSocket):
    await ws.connect()

    while True:
        data = await ws.receive_json()
        logger.debug("consumer of json consumed: %s", data)
        # Do something with the data, which will be parsed json
        # ....


# Produces random data until the client disconnects
async def producer(ws: WebSocket):
    await ws.connect()

    while True:
        await ws.send('%s' % random.randint(0, 1000000))


# Produces random JSON data until the client disconnects
async def producer_of_json(ws: WebSocket):
    await ws.connect()

    while True:
        await ws.send_json({
            'int': random.randint(0, 1000000),
            'uuid1': str(uuid.uuid1()),
            'uuid3': str(uuid.uuid3(uuid.NAMESPACE_DNS, 'apistar websockets')),
            'uuid4': str(uuid.uuid4()),
            'uuid5': str(uuid.uuid5(uuid.NAMESPACE_URL, 'apistar websockets')),
        })

        await asyncio.sleep(0.0)


# A simple one second(ish) timer
async def timer(ws: WebSocket):
    await ws.connect()

    while True:
        await ws.send(datetime.datetime.now().isoformat())
        await asyncio.sleep(1.0)


# Subscribe to a topic of information, simulate a pub/sub pattern.
async def search_subscribe(topic: str, ws: WebSocket):
    if topic not in TOPICS:
        # Make sure it's an approved topic
        await ws.connect(close=True, close_code=status.WS_1007_INALID_DATA)
        return

    await ws.connect()

    salt = ''

    # Use a search result as our data source
    async with aiohttp.ClientSession() as session:
        while True:
            url = 'https://api.duckduckgo.com/?q={}&format=json'.format(topic + salt)

            logger.debug("GET %s", url)
            async with session.get(url) as response:
                response.raise_for_status()
                result = await response.json()

                # Get the results and send them back to the client one at a time.
                for related_topic in result.get('RelatedTopics', []):
                    await ws.send_json(related_topic)
                    # Add some time in between sends to mimic an intermittent data source
                    await asyncio.sleep(random.uniform(1.0, 5.0))

            # Add some salt and query again
            salt = ' ' + random.choice(TOPICS)

    await session.close()


# Let's proxy a crypto API into a websocket
# Free API provided by CryptoCompare @ https://www.cryptocompare.com/api/
async def crypto_price(sym: str, ws: WebSocket):
    url = CRYPTO_URL.format(fsym=sym.upper())

    await ws.connect()

    async with aiohttp.ClientSession() as session:
        while True:
            logger.debug("URL: %s", url)
            async with session.get(url) as response:
                logger.debug("resp: %s", response)
                response.raise_for_status()
                result = await response.json()
                logger.debug("result: %s", result)

                logger.debug("sending: %s", result)
                await ws.send_json(result)
                # The Crypto API is throttled and we need to be nice, so wait a little
                # while before the next request
                logger.debug("waiting...")
                await asyncio.sleep(1.5)


# Behaves just like crypto_price, but relies on the connect() and
# client discconect to be handled by the WebSocketEvents event manager.
# Using something like WebSocketEvents below allows you to avoid the connect/disconnect
# boilerplate if desired.
# Free API provided by CryptoCompare @ https://www.cryptocompare.com/api/
async def crypto_price_managed(sym: str, ws: WebSocket):
    url = CRYPTO_URL.format(fsym=sym.upper())

    async with aiohttp.ClientSession() as session:
        while True:
            logger.debug("URL: %s", url)
            async with session.get(url) as response:
                response.raise_for_status()
                result = await response.json()

                await ws.send_json(result)
                # The Crypto API is throttled and we need to be nice, so wait a little
                # while before the next request
                await asyncio.sleep(1.5)


class WebSocketEvents():
    async def on_request(self, ws: WebSocket, request: WebSocketRequest):
        if request.url.components.path.startswith('/crypto/price/managed/'):
            # Connect the WebSocket, always. Take care of that boilerplate.
            await ws.connect()


routes = [
    Route('/', method='GET', handler=hello),
    Route('/ping_pong', method='GET', handler=ping_pong),
    Route('/consumer', method='GET', handler=consumer),
    Route('/consumer/of/json', method='GET', handler=consumer_of_json),
    Route('/producer', method='GET', handler=producer),
    Route('/producer/of/json', method='GET', handler=producer_of_json),
    Route('/timer', method='GET', handler=timer),
    Route('/search/subscribe/{topic}', method='GET', handler=search_subscribe),
    Route('/crypto/price/{sym}', method='GET', handler=crypto_price),
    Route('/crypto/price/managed/{sym}', method='GET', handler=crypto_price_managed),
]
