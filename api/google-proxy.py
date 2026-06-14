"""
Google API proxy — server side.

The Google Analytics Data / Admin and Search Console APIs don't reliably allow
browser CORS, so calling them from the dashboard fails with "Failed to fetch".
This forwards an authenticated Google API request server-side and returns the
result. Same-origin only. The caller supplies its own OAuth access token.

POST body: { token, url, method (default GET), body (optional JSON) }
Returns:   { status, body }   (body is Google's parsed JSON, or text)
"""
from http.server import BaseHTTPRequestHandler
import json, urllib.request, urllib.error

ALLOWED_ORIGINS = {'https://www.cielohouse.com.au', 'https://cielohouse.com.au'}
GOOGLE_HOSTS = ('googleapis.com',)


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
            req_body = json.loads(self.rfile.read(n).decode()) if n else {}
        except Exception:
            return self._json(400, {'error': 'bad_json'})

        token = req_body.get('token')
        url = req_body.get('url') or ''
        if not token:
            return self._json(401, {'status': 401, 'body': {'error': 'missing_token'}})
        # Only ever proxy to Google.
        if not any(('.' + h) in url or ('//' + h) in url or url.split('/')[2].endswith(h) for h in GOOGLE_HOSTS if len(url.split('/')) > 2):
            return self._json(400, {'error': 'url_not_allowed'})

        method = (req_body.get('method') or 'GET').upper()
        payload = req_body.get('body')
        data = json.dumps(payload).encode() if payload is not None else None
        headers = {'Authorization': 'Bearer ' + token}
        if data is not None:
            headers['Content-Type'] = 'application/json'

        try:
            g = urllib.request.Request(url, method=method, data=data, headers=headers)
            with urllib.request.urlopen(g, timeout=30) as r:
                txt = r.read().decode()
                try:
                    parsed = json.loads(txt)
                except Exception:
                    parsed = {'raw': txt}
                return self._json(200, {'status': r.status, 'body': parsed})
        except urllib.error.HTTPError as e:
            txt = e.read().decode('utf-8', 'ignore')
            try:
                parsed = json.loads(txt)
            except Exception:
                parsed = {'error': txt[:300]}
            return self._json(200, {'status': e.code, 'body': parsed})
        except Exception as e:
            return self._json(200, {'status': 502, 'body': {'error': str(e)}})

    def log_message(self, *a):
        pass
