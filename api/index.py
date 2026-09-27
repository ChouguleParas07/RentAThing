import traceback
import sys

try:
    from app.main import app
except Exception as e:
    err_msg = traceback.format_exc()
    
    async def app(scope, receive, send):
        assert scope['type'] == 'http'
        await send({
            'type': 'http.response.start',
            'status': 500,
            'headers': [
                (b'content-type', b'text/plain'),
            ]
        })
        await send({
            'type': 'http.response.body',
            'body': f"Ultimate Failsafe Error:\n{err_msg}\n\nSys Path:\n{sys.path}".encode('utf-8')
        })
