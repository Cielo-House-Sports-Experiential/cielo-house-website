"""
Case-study image upload (same-origin proxy).
POST /api/cs-upload  with JSON body { data: <base64 or data-URL>, type, ext }
(also accepts a raw binary body with Content-Type = image type).

The dashboard / upload page posts the (already shrunk) image here, and this
function stores it in Supabase Storage with the service-role key, returning the
public URL. Same function style as the working tracking endpoints, so it deploys
to every region (including Sydney).
"""
from http.server import BaseHTTPRequestHandler
import os, json, urllib.request, urllib.error, time, uuid, base64

SB = os.environ.get('SUPABASE_URL', '')
SR = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
BUCKET = 'case-studies'
ADMIN = {'britt@cielohouse.com.au', 'giovana@cielohouse.com.au', 'connect@cielohouse.com.au'}


def verify_admin(auth_header):
    """Only an allow-listed admin (verified Supabase access token) may upload."""
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ', 1)[1]
    try:
        req = urllib.request.Request(SB + '/auth/v1/user', headers={'apikey': SR, 'Authorization': 'Bearer ' + token})
        with urllib.request.urlopen(req, timeout=10) as r:
            u = json.loads(r.read().decode())
        email = (u.get('email') or '').lower()
        return email if email in ADMIN else None
    except Exception:
        return None


class handler(BaseHTTPRequestHandler):
    def _json(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, x-ext, Authorization')
        self.end_headers()

    def do_POST(self):
        if not verify_admin(self.headers.get('Authorization')):
            return self._json(401, {'error': 'unauthorised'})
        try:
            n = int(self.headers.get('Content-Length') or 0)
            if n <= 0:
                return self._json(400, {'error': 'no file received'})
            body = self.rfile.read(n)
            req_ctype = self.headers.get('Content-Type') or ''
            if 'application/json' in req_ctype:
                obj = json.loads(body.decode('utf-8'))
                raw = obj.get('data') or ''
                if raw.startswith('data:') and ',' in raw:
                    raw = raw.split(',', 1)[1]
                data = base64.b64decode(raw)
                ctype = obj.get('type') or 'image/jpeg'
                ext = ''.join(c for c in (obj.get('ext') or 'jpg').lower() if c.isalnum()) or 'jpg'
            else:
                data = body
                ctype = req_ctype or 'image/jpeg'
                ext = ''.join(c for c in (self.headers.get('x-ext') or 'jpg').lower() if c.isalnum()) or 'jpg'
            path = '%d-%s.%s' % (int(time.time()), uuid.uuid4().hex[:8], ext)
            req = urllib.request.Request(
                SB + '/storage/v1/object/' + BUCKET + '/' + path, method='POST', data=data,
                headers={'apikey': SR, 'Authorization': 'Bearer ' + SR, 'Content-Type': ctype, 'x-upsert': 'true'})
            urllib.request.urlopen(req, timeout=30)
            return self._json(200, {'url': SB + '/storage/v1/object/public/' + BUCKET + '/' + path})
        except urllib.error.HTTPError as e:
            return self._json(502, {'error': 'storage ' + str(e.code) + ': ' + e.read().decode('utf-8', 'ignore')[:160]})
        except Exception as e:
            return self._json(500, {'error': str(e)})

    def log_message(self, *a):
        pass
