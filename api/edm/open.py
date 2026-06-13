"""
Cielo House EDM — open tracking pixel.
GET /api/edm/open?s={send_id}  ->  logs the open, returns a 1x1 transparent GIF.
"""
from http.server import BaseHTTPRequestHandler
import os, json, base64, urllib.request, urllib.parse

SB = os.environ.get('SUPABASE_URL', '')
SR = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
PIXEL = base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')


def rpc(fn, args):
    try:
        req = urllib.request.Request(
            SB + '/rest/v1/rpc/' + fn, method='POST',
            data=json.dumps(args).encode(),
            headers={'apikey': SR, 'Authorization': 'Bearer ' + SR, 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.read().decode()
    except Exception:
        return None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        sid = q.get('s', [''])[0]
        if sid:
            rpc('edm_log_open', {'p_send': sid})
        self.send_response(200)
        self.send_header('Content-Type', 'image/gif')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Content-Length', str(len(PIXEL)))
        self.end_headers()
        self.wfile.write(PIXEL)

    def log_message(self, *a):
        pass
