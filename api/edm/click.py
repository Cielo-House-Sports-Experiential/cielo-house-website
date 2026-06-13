"""
Cielo House EDM — click tracking + redirect.
GET /api/edm/click?s={send_id}&sec={section_id}
Logs the per-section click and 302s to the section's destination. The destination
is read from the DB (and validated to belong to the campaign), never from the URL,
so this can't be abused as an open redirect.
"""
from http.server import BaseHTTPRequestHandler
import os, json, urllib.request, urllib.parse, hashlib

SB = os.environ.get('SUPABASE_URL', '')
SR = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
FALLBACK = 'https://www.cielohouse.com.au/'


def rpc(fn, args):
    try:
        req = urllib.request.Request(
            SB + '/rest/v1/rpc/' + fn, method='POST',
            data=json.dumps(args).encode(),
            headers={'apikey': SR, 'Authorization': 'Bearer ' + SR, 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.read().decode().strip()
    except Exception:
        return None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        sid = q.get('s', [''])[0]
        sec = q.get('sec', [''])[0]
        ua = (self.headers.get('User-Agent', '') or '')[:300]
        ip = (self.headers.get('x-forwarded-for', '') or '').split(',')[0].strip()
        ip_hash = hashlib.sha256((ip + '|cielo').encode()).hexdigest()[:32] if ip else None
        dest = None
        if sid and sec:
            res = rpc('edm_log_click', {'p_send': sid, 'p_section': sec, 'p_ua': ua, 'p_ip': ip_hash})
            if res and res != 'null':
                try:
                    dest = json.loads(res)
                except Exception:
                    dest = res
        if not dest or not (str(dest).startswith('http://') or str(dest).startswith('https://')):
            dest = FALLBACK
        self.send_response(302)
        self.send_header('Location', dest)
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()

    def log_message(self, *a):
        pass
