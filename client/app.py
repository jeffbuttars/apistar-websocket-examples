#!/usr/bin/env python
# encoding: utf-8

import logging
import asyncio
import aiohttp

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

url = 'http://localhost:8000'
url_1000 = 'http://localhost:8000/1000'


async def run():
    logger.debug("Begining client session")
    session = aiohttp.ClientSession()

    logger.debug("connecting")
    async with session.ws_connect(url_1000) as ws:
        logger.debug("receiving")
        async for msg in ws:
            msg = await ws.receive()
            logger.debug("received: %s: %s", msg, msg.data)
            if msg.type != aiohttp.WSMsgType.TEXT:
                logger.debug("closing")
                await ws.close()
                return


def main():
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run())
        # Add a small bump to allow connections to clean up
        loop.run_until_complete(asyncio.sleep(0))
        loop.close()
    except KeyboardInterrupt:
        logger.debug("Keyboard Interrupt")
        loop.close()


if __name__ == '__main__':
    main()
