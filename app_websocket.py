import asyncio
import websockets

async def checkPose(websocket, path):
    try:
        async for message in websocket:
            print ('Server received message :' + message)
            await websocket.send('Server echoed message :' + message)
    except Exception as e:
        print(str(e) + ' Something went wrong. Someone needs to know')

try:
    start_server = websockets.serve(checkPose, None, 5001)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
except:
    print('Websockets server cannot start. Someone needs to know')
















