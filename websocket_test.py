import asyncio
import websockets
import json


url = 'wss://ws.backpack.exchange'

async def bp_websocket():
    async with websockets.connect(url) as websocket:
        while True:
            try:
                pass
            except websockets.ConnectionClosed:
                print("连接中断，尝试重连...")
                break
            except Exception as e:
                print(f"错误: {e}")

# 启动连接
asyncio.get_event_loop().run_until_complete(bp_websocket())
