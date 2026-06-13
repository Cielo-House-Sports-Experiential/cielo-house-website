"""
Cielo House EDM — one-click unsubscribe.
GET or POST /api/edm/unsubscribe?t={token}
Suppresses the subscriber and renders a branded confirmation. POST supports the
email clients' one-click List-Unsubscribe-Post.
"""
from http.server import BaseHTTPRequestHandler
import os, json, urllib.request, urllib.parse

SB = os.environ.get('SUPABASE_URL', '')
SR = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')


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


def page(heading, body):
    return (
        '<!DOCTYPE html><html lang="en-AU"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>' + heading + ' | Cielo House</title>'
        '<style>body{font-family:Poppins,Arial,sans-serif;background:#2B317B;color:#fff;display:flex;'
        'align-items:center;justify-content:center;min-height:100vh;margin:0;text-align:center;padding:2rem}'
        '.box{max-width:480px}h1{font-weight:600;font-size:1.5rem;margin-bottom:1rem}'
        'p{color:rgba(255,255,255,0.82);line-height:1.7}a{color:#86A8D6}</style></head>'
        '<body><div class="box"><h1>' + heading + '</h1><p>' + body + '</p>'
        '<p><a href="https://www.cielohouse.com.au/">Return to cielohouse.com.au</a></p></div></body></html>')


class handler(BaseHTTPRequestHandler):
    def _do(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        token = q.get('t', [''])[0]
        ok = bool(token) and (rpc('edm_unsubscribe', {'p_token': token}) == 'true')
        if ok:
            html = page('You have been unsubscribed',
                        "You won't receive any more emails from Cielo House Experiential &amp; Events. Sorry to see you go.")
        else:
            html = page('Link not recognised',
                        'This unsubscribe link is invalid or has already been used. If you keep receiving emails, contact connect@cielohouse.com.au.')
        b = html.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        self._do()

    def do_POST(self):
        self._do()

    def log_message(self, *a):
        pass
