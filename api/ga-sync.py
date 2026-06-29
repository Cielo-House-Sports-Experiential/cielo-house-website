"""
Cielo House — Google Analytics sync (server-side).
POST /api/ga-sync   (same-origin, or ?token=<RUN_TOKEN> for cron)

Refreshes Google Analytics + Search Console figures on a schedule using the
Google credentials saved in dashboard_secrets, and merges them into the
dashboard_kv 'ch_stats' record that every dashboard viewer reads. This keeps
the numbers fresh for everyone (incl. Gio) without anyone opening the dashboard
or touching Google in the browser.
"""
import os, json, datetime, urllib.request, urllib.parse, urllib.error
from http.server import BaseHTTPRequestHandler

SB = os.environ.get('SUPABASE_URL', 'https://nkabuhbkuzcxajzrlenj.supabase.co')
SR = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
RUN_TOKEN = 'cielo-aivis-run-2026-9f3ac71b'
GA4_PROPERTY_ID = '503383473'
GSC_SITES = ['sc-domain:cielohouse.com.au', 'https://www.cielohouse.com.au/']
ALLOWED_ORIGINS = {'https://www.cielohouse.com.au', 'https://cielohouse.com.au'}


def _sb_headers(extra=None):
    h = {'apikey': SR, 'Authorization': 'Bearer ' + SR, 'Content-Type': 'application/json'}
    if extra:
        h.update(extra)
    return h


def _http(url, method='POST', headers=None, body=None, raw_body=None, timeout=30):
    if raw_body is not None:
        data = raw_body
    else:
        data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        txt = r.read().decode().strip()
        return json.loads(txt) if txt else None


def get_secrets():
    rows = _http(SB + '/rest/v1/dashboard_secrets?id=eq.main&select=vals',
                 method='GET', headers=_sb_headers(), timeout=10)
    return (rows[0]['vals'] if rows else {}) or {}


def refresh_access_token(client_id, client_secret, refresh_token):
    data = urllib.parse.urlencode({
        'client_id': client_id, 'client_secret': client_secret,
        'refresh_token': refresh_token, 'grant_type': 'refresh_token',
    }).encode()
    j = _http('https://oauth2.googleapis.com/token',
              headers={'Content-Type': 'application/x-www-form-urlencoded'},
              raw_body=data, timeout=20)
    return j.get('access_token')


def _ga(token, prop, body):
    url = 'https://analyticsdata.googleapis.com/v1beta/properties/%s:runReport' % prop
    return _http(url, headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'},
                 body=body, timeout=30)


def ga4_main(token, prop):
    return _ga(token, prop, {
        'dateRanges': [
            {'startDate': '30daysAgo', 'endDate': 'today', 'name': 'current'},
            {'startDate': '60daysAgo', 'endDate': '31daysAgo', 'name': 'previous'},
        ],
        'metrics': [{'name': 'sessions'}, {'name': 'activeUsers'}, {'name': 'screenPageViews'}],
    })


def ga4_events(token, prop):
    try:
        return _ga(token, prop, {
            'dateRanges': [{'startDate': '30daysAgo', 'endDate': 'today'}],
            'dimensions': [{'name': 'eventName'}],
            'metrics': [{'name': 'eventCount'}],
            'dimensionFilter': {'filter': {'fieldName': 'eventName',
                'stringFilter': {'value': 'schedule_call', 'matchType': 'EXACT'}}},
        })
    except Exception:
        return None


def gsc(token):
    end = datetime.date.today() - datetime.timedelta(days=3)
    start = end - datetime.timedelta(days=28)
    body = {'startDate': start.isoformat(), 'endDate': end.isoformat(),
            'dimensions': ['query'], 'rowLimit': 5}
    for site in GSC_SITES:
        try:
            url = ('https://www.googleapis.com/webmasters/v3/sites/'
                   + urllib.parse.quote(site, safe='') + '/searchAnalytics/query')
            return _http(url, headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'},
                         body=body, timeout=25)
        except Exception:
            continue
    return None


def parse(main, events, gscdata):
    out = {}
    rows = (main or {}).get('rows', []) if main else []
    if rows:
        cur = rows[0]['metricValues']
        out['sessions'] = int(float(cur[0]['value'] or 0))
        out['visitors'] = int(float(cur[1]['value'] or 0))
        out['pageviews'] = int(float(cur[2]['value'] or 0))
        if len(rows) >= 2:
            prev = rows[1]['metricValues']
            ps = int(float(prev[0]['value'] or 0))
            pv = int(float(prev[1]['value'] or 0))
            if ps >= 10:
                out['sessionsPct'] = max(-999, min(999, round((out['sessions'] - ps) / ps * 100)))
            if pv >= 10:
                out['visitorsPct'] = max(-999, min(999, round((out['visitors'] - pv) / pv * 100)))
    erows = (events or {}).get('rows', []) if events else []
    if erows:
        out['clicks'] = int(float(erows[0]['metricValues'][0]['value'] or 0))
    grows = (gscdata or {}).get('rows', []) if gscdata else []
    if grows:
        out['googlePeriod'] = 'Last 28 days · ' + datetime.datetime.utcnow().strftime('%b %Y')
        for i, row in enumerate(grows[:3]):
            out['gq%d' % (i + 1)] = {'query': row['keys'][0], 'imp': round(row['impressions']),
                                     'clicks': round(row['clicks']), 'pos': '%.1f' % row['position']}
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    out['updatedAt'] = now
    out['syncedAt'] = now
    return out


def merge_into_ch_stats(ga_fields):
    rows = _http(SB + "/rest/v1/dashboard_kv?k=eq.ch_stats&select=v",
                 method='GET', headers=_sb_headers(), timeout=10)
    existing = (rows[0]['v'] if rows else {}) or {}
    existing.update(ga_fields)
    _http(SB + '/rest/v1/dashboard_kv?on_conflict=k', method='POST',
          headers=_sb_headers({'Prefer': 'resolution=merge-duplicates,return=minimal'}),
          body={'k': 'ch_stats', 'v': existing,
                'updated_at': datetime.datetime.utcnow().isoformat() + 'Z'}, timeout=20)


def run():
    sec = get_secrets()
    cid = sec.get('ch_google_client_id', '')
    csec = sec.get('ch_google_client_secret', '')
    rtok = sec.get('ch_ga_refresh_token', '')
    if not (cid and csec and rtok):
        return {'error': 'Google credentials not saved (client id/secret/refresh token).'}
    token = refresh_access_token(cid, csec, rtok)
    if not token:
        return {'error': 'Could not refresh Google access token.'}
    main = ga4_main(token, GA4_PROPERTY_ID)
    events = ga4_events(token, GA4_PROPERTY_ID)
    gscdata = gsc(token)
    fields = parse(main, events, gscdata)
    if 'sessions' not in fields:
        return {'error': 'GA4 returned no rows', 'fields': fields}
    merge_into_ch_stats(fields)
    return {'ok': True, 'sessions': fields.get('sessions'), 'visitors': fields.get('visitors'),
            'pageviews': fields.get('pageviews'), 'clicks': fields.get('clicks'),
            'gsc_queries': sum(1 for k in fields if k.startswith('gq')), 'synced_at': fields['syncedAt']}


class handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(b)

    def _authed(self):
        origin = (self.headers.get('Origin') or '').rstrip('/')
        if origin and origin in ALLOWED_ORIGINS:
            return True
        ref = self.headers.get('Referer') or ''
        if any(ref.startswith(o) for o in ALLOWED_ORIGINS):
            return True
        q = self.path.split('?', 1)[1] if '?' in self.path else ''
        return ('token=' + RUN_TOKEN) in q

    def do_POST(self):
        if not SR:
            return self._send(500, {'error': 'SUPABASE_SERVICE_ROLE_KEY not set'})
        if not self._authed():
            return self._send(403, {'error': 'forbidden'})
        try:
            return self._send(200, run())
        except urllib.error.HTTPError as e:
            try:
                detail = json.loads(e.read().decode())
            except Exception:
                detail = str(e)
            return self._send(500, {'error': 'google/api error', 'detail': detail})
        except Exception as e:
            return self._send(500, {'error': str(e)})

    def do_GET(self):
        self.do_POST()
