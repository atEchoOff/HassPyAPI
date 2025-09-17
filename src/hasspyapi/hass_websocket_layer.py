import json
import websockets

class HassWebSocketLayer:
    def __init__(self, ws, ws_url, ws_headers):
        '''
        Layer between hass web socket and Python
        '''
        self.ws = ws
        self.ws_url = ws_url
        self.ws_headers = ws_headers

    @classmethod
    async def authorize(cls, ws_url, ws_headers):
        '''
        Authorize a websocket client
        '''
        # Recieve first message. This is likely auth_required
        ws = await websockets.connect(ws_url, ping_interval=20, ping_timeout=20, close_timeout=10)
        first = json.loads(await ws.recv())

        if first.get("type") == "auth_required":
            await ws.send(json.dumps(ws_headers))
            auth_resp = json.loads(await ws.recv())
            if auth_resp.get("type") != "auth_ok":
                raise RuntimeError(f"Auth failed: {auth_resp}")
        else:
            # Server did not ask for auth... there is some issue
            raise RuntimeError(f"Server auth failed: {first}")
        
        return cls(ws, ws_url, ws_headers)
    
    async def subscribe(self):
        '''
        Subscribe to all events via the hass web socket
        '''
        await self.ws.send(json.dumps({"id": 4, "type": "subscribe_events"}))

        resp = json.loads(await self.ws.recv())

        if resp.get("id") != 4:
            raise RuntimeError(f"Websocket call id 4 mismatch: recv id was {resp.get("id")}")
        if not resp.get("success", True):
            raise RuntimeError(f"Websocket call 4 failed: {resp}")
        return resp.get("result", [])
    
    async def call(self, cmd_type, msg_id):
        '''
        Get data from various endpoints, ensuring correct msg_id
        '''
        await self.ws.send(json.dumps({"id": msg_id, "type": cmd_type}))
        
        resp = json.loads(await self.ws.recv())

        if resp.get("id") != msg_id:
            raise RuntimeError(f"Websocket call id {msg_id} mismatch: recv id was {resp.get("id")}")
        if not resp.get("success", True):
            raise RuntimeError(f"Websocket call {cmd_type} failed: {resp}")
        return resp.get("result", [])
    
    async def recv(self):
        '''
        Recieve a message and jsonify
        '''
        return json.loads(await self.ws.recv())
    
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.ws.close()