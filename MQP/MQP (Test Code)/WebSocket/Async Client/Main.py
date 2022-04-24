from WSClient import WebSocketClient
import asyncio

if __name__ == '__main__':
    client = WebSocketClient()
    loop = asyncio.get_event_loop()

    connection = loop.run_until_complete(client.connect())

    loop.run_until_complete(client.close())
    