"""
Cielo House EDM — send engine.
POST /api/edm/send   (Authorization: Bearer <supabase access token>)
Body: { "campaign_id": "...", "mode": "test"|"now", "test_emails": ["..."] }

- mode "test": sends [TEST] copies to the given addresses; no edm_sends rows, no stats.
- mode "now":  sends to all subscribed recipients, writes edm_sends rows (with tracking),
               sets List-Unsubscribe headers, marks the campaign sent.

Admin-only: verifies the Supabase access token belongs to an allow-listed admin.
"""
from http.server import BaseHTTPRequestHandler
import os, json, urllib.request, urllib.error, html as htmlmod
from datetime import datetime, timezone

SB = os.environ.get('SUPABASE_URL', '')
SR = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
RESEND = os.environ.get('RESEND_API_KEY', '')
SCHED_TOKEN = os.environ.get('EDM_SCHEDULER_TOKEN', '')
BASE = os.environ.get('EDM_TRACKING_BASE_URL', 'https://www.cielohouse.com.au')
ADMIN = {'britt@cielohouse.com.au', 'giovana@cielohouse.com.au', 'connect@cielohouse.com.au'}
FROM = 'Cielo House Experiential & Events <connect@cielohouse.com.au>'


def sb(method, path, body=None, prefer=None):
    req = urllib.request.Request(SB + '/rest/v1/' + path, method=method,
                                 data=(json.dumps(body).encode() if body is not None else None))
    req.add_header('apikey', SR); req.add_header('Authorization', 'Bearer ' + SR)
    req.add_header('Content-Type', 'application/json')
    if prefer:
        req.add_header('Prefer', prefer)
    with urllib.request.urlopen(req, timeout=20) as r:
        t = r.read().decode()
        return json.loads(t) if t else None


def verify_admin(auth_header):
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


def esc(s):
    return htmlmod.escape(s or '', quote=True)


def build_email(camp, sections, send_id, token):
    pre = esc(camp.get('preview_text') or '')
    rows = []
    for sec in sections:
        imgtag = ('<img src="' + esc(sec.get('image_url') or '') + '" alt="' + esc(sec.get('image_alt') or '') +
                  '" width="1200" style="display:block;width:100%;max-width:1200px;height:auto;border:0;" />')
        if sec.get('link_url'):
            href = BASE + '/api/edm/click?s=' + send_id + '&sec=' + sec['id']
            imgtag = '<a href="' + href + '" target="_blank">' + imgtag + '</a>'
        rows.append('<tr><td style="padding:0;font-size:0;line-height:0;">' + imgtag + '</td></tr>')
    unsub = BASE + '/api/edm/unsubscribe?t=' + (token or '')
    pixel = '<img src="' + BASE + '/api/edm/open?s=' + send_id + '" width="1" height="1" alt="" style="display:none;" />'
    footer = ('<tr><td style="padding:24px 20px;font-family:Arial,Helvetica,sans-serif;font-size:12px;'
              'color:#888;text-align:center;line-height:1.7;">'
              'Cielo House Experiential &amp; Events<br>'
              '<a href="mailto:connect@cielohouse.com.au" style="color:#888;">connect@cielohouse.com.au</a><br><br>'
              'You are receiving this because you subscribed at cielohouse.com.au.<br>'
              '<a href="' + unsub + '" style="color:#888;text-decoration:underline;">Unsubscribe</a>'
              '</td></tr>')
    html = ('<!DOCTYPE html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="color-scheme" content="light"></head>'
            '<body style="margin:0;padding:0;background:#f4f4f4;">'
            '<div style="display:none;max-height:0;overflow:hidden;opacity:0;">' + pre + '</div>'
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;">'
            '<tr><td align="center" style="padding:0;">'
            '<table role="presentation" width="1200" cellpadding="0" cellspacing="0" '
            'style="width:100%;max-width:1200px;background:#ffffff;">' + ''.join(rows) + footer +
            '</table></td></tr></table>' + pixel + '</body></html>')
    txt = [camp.get('preview_text') or camp.get('subject') or '']
    for sec in sections:
        if sec.get('link_url'):
            txt.append((sec.get('image_alt') or 'Link') + ': ' + sec['link_url'])
    txt += ['', 'Cielo House Experiential & Events — connect@cielohouse.com.au', 'Unsubscribe: ' + unsub]
    return html, '\n'.join(txt)


def resend_send(obj):
    if not RESEND:
        raise Exception('RESEND_API_KEY is not set on the server')
    req = urllib.request.Request('https://api.resend.com/emails', method='POST', data=json.dumps(obj).encode(),
                                 headers={'Authorization': 'Bearer ' + RESEND, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail = ''
        try:
            detail = e.read().decode()[:400]
        except Exception:
            pass
        raise Exception('Resend rejected the email (' + str(e.code) + '): ' + detail)


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
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_POST(self):
        sched = self.headers.get('X-Scheduler-Token') or ''
        if not (verify_admin(self.headers.get('Authorization')) or (SCHED_TOKEN and sched == SCHED_TOKEN)):
            return self._json(401, {'error': 'unauthorised'})
        try:
            n = int(self.headers.get('Content-Length') or 0)
            body = json.loads(self.rfile.read(n).decode()) if n else {}
        except Exception:
            return self._json(400, {'error': 'bad_json'})
        cid = body.get('campaign_id')
        mode = body.get('mode', 'test')
        if not cid:
            return self._json(400, {'error': 'campaign_id required'})
        try:
            camps = sb('GET', 'edm_campaigns?id=eq.' + cid + '&select=*')
            if not camps:
                return self._json(404, {'error': 'campaign not found'})
            camp = camps[0]
            sections = sb('GET', 'edm_campaign_sections?campaign_id=eq.' + cid + '&order=position.asc&select=*') or []
            if not sections:
                return self._json(400, {'error': 'campaign has no image sections'})
            subject = camp.get('subject') or '(no subject)'

            if mode == 'test':
                tests = [e.strip() for e in (body.get('test_emails') or []) if e and e.strip()]
                if not tests:
                    return self._json(400, {'error': 'test_emails required'})
                sent = 0
                for em in tests:
                    h, t = build_email(camp, sections, 'test', 'test')
                    resend_send({'from': FROM, 'to': [em], 'subject': '[TEST] ' + subject, 'html': h, 'text': t})
                    sent += 1
                return self._json(200, {'ok': True, 'mode': 'test', 'sent': sent})

            # mode == 'now'
            recips = sb('GET', 'subscribers?status=eq.subscribed&select=id,email,unsubscribe_token') or []
            if not recips:
                return self._json(400, {'error': 'no subscribed recipients'})
            sent = failed = 0
            for sub_row in recips:
                ins = sb('POST', 'edm_sends', {'campaign_id': cid, 'subscriber_id': sub_row['id'],
                                               'email': sub_row['email'], 'status': 'queued'},
                         prefer='return=representation')
                send_id = ins[0]['id']
                tok = sub_row.get('unsubscribe_token') or ''
                h, t = build_email(camp, sections, send_id, tok)
                try:
                    r = resend_send({'from': FROM, 'to': [sub_row['email']], 'subject': subject, 'html': h, 'text': t,
                                     'headers': {'List-Unsubscribe': '<' + BASE + '/api/edm/unsubscribe?t=' + tok + '>',
                                                 'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click'}})
                    sb('PATCH', 'edm_sends?id=eq.' + send_id,
                       {'status': 'sent', 'resend_message_id': r.get('id'),
                        'sent_at': datetime.now(timezone.utc).isoformat()})
                    sent += 1
                except Exception:
                    sb('PATCH', 'edm_sends?id=eq.' + send_id, {'status': 'failed'})
                    failed += 1
            sb('PATCH', 'edm_campaigns?id=eq.' + cid,
               {'status': 'sent', 'sent_at': datetime.now(timezone.utc).isoformat(),
                'stats': {'recipients': len(recips), 'sent': sent, 'failed': failed}})
            return self._json(200, {'ok': True, 'mode': 'now', 'recipients': len(recips), 'sent': sent, 'failed': failed})
        except Exception as e:
            return self._json(500, {'error': str(e)})

    def log_message(self, *a):
        pass
