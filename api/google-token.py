"""
Google OAuth token exchange — server side.

The dashboard's Google Analytics / Search Console connection used to call
https://oauth2.googleapis.com/token directly from the browser, but Google's
token endpoint does not allow CORS, so it always failed ("Failed to fetch").
This function performs the exchange server-side (no CORS), for both:
  - mode "code":    authorization_code  -> access_token + refresh_token
  - mode "refresh": refresh_token        -> fresh access_token

Same-origin only. The Google client_id/secret are supplied by the (admin-only)
dashboard; this endpoint just proxies the exchange.
"""
from http.server import BaseHTTPRequestHandler
import json, urllib.request, urllib.parse, urllib.error

ALLOWED_ORIGINS = {'https://www.cielohouse.com.au', 'https://cielohouse.com.au'}


def _origin_ok(headers):
    origin = (headers.get('Origin') or '').rstrip('/')
    if origin:
        return origin in ALLOWED_ORIGINS
    ref = headers.get('Referer') or ''
    return any(ref.startswith(o) for o in ALLOWED_ORIGINS)


class handler(BaseHTTPRequestHandler):
    def _cors(self):
        origin = (self.headers.get('Origin') or '').rstrip('/')
        self.send_header('Access-Control-Allow-Origin', origin if origin in ALLOWED_ORIGINS else 'https://www.cielohouse.com.au')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _json(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if not _origin_ok(self.headers):
            return self._json(403, {'error': 'forbidden'})
        try:
            n = int(self.headers.get('Content-Length') or 0)
            body = json.loads(self.rfile.read(n).decode()) if n else {}
        except Exception:
            return self._json(400, {'error': 'bad_json'})

        cid = body.get('client_id')
        sec = body.get('client_secret')
        if not cid or not sec:
            return self._json(400, {'error': 'missing_client', 'error_description': 'client_id and client_secret are required'})

        if body.get('mode') == 'refresh':
            form = {'grant_type': 'refresh_token', 'refresh_token': body.get('refresh_token', ''), 'client_id': cid, 'client_secret': sec}
        else:
            form = {'grant_type': 'authorization_code', 'code': body.get('code', ''), 'client_id': cid, 'client_secret': sec, 'redirect_uri': body.get('redirect_uri', 'postmessage')}

        try:
            req = urllib.request.Request('https://oauth2.googleapis.com/token', method='POST',
                                         data=urllib.parse.urlencode(form).encode(),
                                         headers={'Content-Type': 'application/x-www-form-urlencoded'})
            with urllib.request.urlopen(req, timeout=20) as r:
                return self._json(200, json.loads(r.read().decode()))
        except urllib.error.HTTPError as e:
            try:
                return self._json(e.code, json.loads(e.read().decode() or '{}'))
            except Exception:
                return self._json(e.code, {'error': 'google_error', 'error_description': 'HTTP ' + str(e.code)})
        except Exception as e:
            return self._json(502, {'error': 'exchange_failed', 'error_description': str(e)})

    def log_message(self, *a):
        pass
