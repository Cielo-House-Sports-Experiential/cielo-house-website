"""
Case-study image upload — same-origin proxy.
POST /api/cs-upload   (raw image bytes as the body; Content-Type = the image type;
optional x-ext header for the file extension)

The dashboard posts the image here (to cielohouse.com.au itself), and THIS function
uploads it to Supabase Storage server-side with the service-role key, then returns
the public URL. Going through our own domain avoids the browser/extension blocks that
were killing the direct Supabase upload ("Failed to fetch").
"""
from http.server import BaseHTTPRequestHandler
import os, json, urllib.request, time, uuid

SB = os.environ.get('SUPABASE_URL', '')
SR = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
BUCKET = 'case-studies'


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
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, x-ext')
        self.end_headers()

    def do_POST(self):
        try:
            n = int(self.headers.get('Content-Length') or 0)
            if n <= 0:
                return self._json(400, {'error': 'no file received'})
            if n > 30 * 1024 * 1024:
                return self._json(413, {'error': 'image too large (max 25MB)'})
            data = self.rfile.read(n)
            ctype = self.headers.get('Content-Type') or 'image/jpeg'
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
