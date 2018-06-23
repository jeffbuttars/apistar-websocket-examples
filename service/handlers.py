import asyncio
import datetime
import random
import uuid
import logging

from apistar import WebSocket, Route, http
from apistar.server.websocket import status
from apistar.exceptions import WebSocketDisconnect

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def hello(ws: WebSocket):
    await ws.connect()
    await ws.send('Hello World!')


async def ping_pong(ws: WebSocket):
    # For as long as the client sends a 'ping', we'll send a pong.
    # If the client doesn't send a 'ping', we close with an error
    # If the client disconnects, we finish
    await ws.connect()

    while True:
        try:
            await ping = await ws.receive()

            if ping != 'ping':
                ws.close(code=status.WS_1002_PROT_ERROR)
                return

            await ws.send('pong')
        except WebSocketDisconnect:
            # Client disconnected, we're done
            return


async def consumer(ws: WebSocket):
    # Simply accepts all incoming data until the client
    # closes.
    await ws.connect()

    while True:
        try:
            await data = await ws.receive()

            # Do something with the data
            # ....
        except WebSocketDisconnect:
            # Client disconnected, we're done
            return


async def consumer_of_json(ws: WebSocket):
    # Simply accepts all incoming json data until the client
    # closes.
    await ws.connect()

    while True:
        try:
            await data = await ws.receive_json()

            # Do something with the data, which will be parsed json
            # ....
        except WebSocketDisconnect:
            # Client disconnected, we're done
            return


async def producer(ws: WebSocket):
    # Produces random data until the client disconnects
    await ws.connect()

    while True:
        try:
            await ws.send('%s' % random.randint())

            # Wait for a short time before sending more data
            await asyncio.sleep(0.05)
        except WebSocketDisconnect:
            # Client disconnected, we're done
            return


async def producer_of_json(ws: WebSocket):
    # Produces random data until the client disconnects
    await ws.connect()

    while True:
        try:
            await ws.send_json({
                'int': random.randint(),
                'uuid': uuid.uuid4(),
            })

            # Wait for a short time before sending more data
            await asyncio.sleep(0.05)
        except WebSocketDisconnect:
            # Client disconnected, we're done
            return


async def timer(ws: WebSocket):
    await ws.connect()

    while True:
        try:
            await ws.send(datetime.datetime.now().isoformat())

            await asyncio.sleep()
        except WebSocketDisconnect:
            # Client disconnected, we're done
            return


routes = [
    Route('/', method='GET', handler=hello),
    Route('/ping_pong', method='GET', handler=ping_pong),
    Route('/consumer', method='GET', handler=consumer),
    Route('/consumer/of/json', method='GET', handler=consumer_of_json),
    Route('/producer', method='GET', handler=producer),
    Route('/producer/of/json', method='GET', handler=producer_of_json),
    Route('/timer', method='GET', handler=timer),
]
