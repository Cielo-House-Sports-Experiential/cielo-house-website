"""
Cielo House EDM — scheduled-send runner.
GET /api/edm/run-scheduled   (header: X-Scheduler-Token: <EDM_SCHEDULER_TOKEN>)

Fired every minute by the dispatch-mini ticker. Finds every campaign whose
status is 'scheduled' and whose scheduled_at has arrived, claims it (status
'sending' so the next tick can't double-send), then triggers the normal send
engine (api/edm/send, mode 'now') for it. On failure the campaign is flagged
'send_failed' so it surfaces in the dashboard rather than retrying forever.
"""
from http.server import BaseHTTPRequestHandler
import os, json, urllib.request
from datetime import datetime, timezone

SB = os.environ.get('SUPABASE_URL', '')
SR = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
SCHED_TOKEN = os.environ.get('EDM_SCHEDULER_TOKEN', '')
BASE = os.environ.get('EDM_TRACKING_BASE_URL', 'https://www.cielohouse.com.au')


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


def trigger_send(cid):
    req = urllib.request.Request(BASE + '/api/edm/send', method='POST',
                                 data=json.dumps({'campaign_id': cid, 'mode': 'now'}).encode(),
                                 headers={'Content-Type': 'application/json', 'X-Scheduler-Token': SCHED_TOKEN})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


class handler(BaseHTTPRequestHandler):
    def _json(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _run(self):
        token = self.headers.get('X-Scheduler-Token') or ''
        if not SCHED_TOKEN or token != SCHED_TOKEN:
            return self._json(401, {'error': 'unauthorised'})
        now = datetime.now(timezone.utc).isoformat()
        try:
            due = sb('GET', "edm_campaigns?status=eq.scheduled&scheduled_at=lte." + now + "&select=id,subject") or []
        except Exception as e:
            return self._json(500, {'error': 'query_failed: ' + str(e)})
        results = []
        for c in due:
            cid = c['id']
            # Claim so a second tick can't pick it up while this send runs.
            try:
                sb('PATCH', 'edm_campaigns?id=eq.' + cid + '&status=eq.scheduled',
                   {'status': 'sending'}, prefer='return=minimal')
            except Exception:
                continue
            try:
                r = trigger_send(cid)
                results.append({'id': cid, 'ok': bool(r.get('ok')), 'sent': r.get('sent')})
            except Exception as e:
                sb('PATCH', 'edm_campaigns?id=eq.' + cid, {'status': 'send_failed'})
                results.append({'id': cid, 'ok': False, 'error': str(e)})
        return self._json(200, {'ok': True, 'due': len(due), 'results': results})

    def do_GET(self):
        self._run()

    def do_POST(self):
        self._run()

    def log_message(self, *a):
        pass
