"""
Cielo House EDM — click tracking + redirect.
GET /api/edm/click?s={send_id}&sec={section_id}[&i={slice_index}]
302s to the link's destination and, for real sends, records the click. The
destination is read from the DB (the section's stored link, or slice i of a
multi-link "row" section), never from the URL, so this is not an open redirect.

Per-link counts live on edm_campaigns.stats.link_clicks (keyed by section, or
section:slice), so the dashboard can show how many clicked each link — including
the separate Instagram / LinkedIn icons. Clicks arrive spread over days at ~27
recipients, so the read-modify-write on stats is not a contention risk.
"""
from http.server import BaseHTTPRequestHandler
import os, json, urllib.request, urllib.parse, hashlib

SB = os.environ.get('SUPABASE_URL', '')
SR = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
FALLBACK = 'https://www.cielohouse.com.au/'
H = {'apikey': SR, 'Authorization': 'Bearer ' + SR}


def rpc(fn, args):
    try:
        req = urllib.request.Request(
            SB + '/rest/v1/rpc/' + fn, method='POST', data=json.dumps(args).encode(),
            headers=dict(H, **{'Content-Type': 'application/json'}))
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.read().decode().strip()
    except Exception:
        return None


def get_section(sec):
    try:
        req = urllib.request.Request(
            SB + '/rest/v1/edm_campaign_sections?id=eq.' + urllib.parse.quote(sec) +
            '&select=campaign_id,link_url,image_alt', headers=H)
        with urllib.request.urlopen(req, timeout=8) as r:
            rows = json.loads(r.read().decode())
        return rows[0] if rows else None
    except Exception:
        return None


def resolve(section, i):
    # -> (dest, label, url). Slice i of a JSON "row" section, else the plain link.
    link = (section or {}).get('link_url') or ''
    if link.startswith('{'):
        try:
            row = json.loads(link).get('row') or []
        except Exception:
            row = []
        if i is not None and 0 <= i < len(row):
            href = row[i].get('href')
            if href:
                return href, (row[i].get('label') or href), href
        return None, None, None
    if link:
        return link, ((section or {}).get('image_alt') or link), link
    return None, None, None


def bump_link_click(campaign_id, key, label, url):
    # Increment stats.link_clicks[key].clicks on the campaign.
    try:
        req = urllib.request.Request(
            SB + '/rest/v1/edm_campaigns?id=eq.' + urllib.parse.quote(campaign_id) + '&select=stats', headers=H)
        with urllib.request.urlopen(req, timeout=8) as r:
            rows = json.loads(r.read().decode())
        stats = (rows[0].get('stats') if rows else None) or {}
        lc = stats.get('link_clicks') or {}
        entry = lc.get(key) or {'clicks': 0}
        entry['clicks'] = int(entry.get('clicks', 0)) + 1
        entry['label'] = label
        entry['url'] = url
        lc[key] = entry
        stats['link_clicks'] = lc
        req2 = urllib.request.Request(
            SB + '/rest/v1/edm_campaigns?id=eq.' + urllib.parse.quote(campaign_id), method='PATCH',
            data=json.dumps({'stats': stats}).encode(),
            headers=dict(H, **{'Content-Type': 'application/json', 'Prefer': 'return=minimal'}))
        urllib.request.urlopen(req2, timeout=8).read()
    except Exception:
        pass


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        sid = q.get('s', [''])[0]
        sec = q.get('sec', [''])[0]
        raw_i = q.get('i', [None])[0]
        i = None
        if raw_i is not None:
            try:
                i = int(raw_i)
            except Exception:
                i = None
        ua = (self.headers.get('User-Agent', '') or '')[:300]
        ip = (self.headers.get('x-forwarded-for', '') or '').split(',')[0].strip()
        ip_hash = hashlib.sha256((ip + '|cielo').encode()).hexdigest()[:32] if ip else None

        section = get_section(sec) if sec else None
        dest, label, url = resolve(section, i)
        key = (sec + ':' + str(i)) if (sec and i is not None) else sec

        # Record the click for real sends only (a test has no send row; logging it
        # would corrupt the campaign's stats).
        if sid and sec and sid != 'test':
            rpc('edm_log_click', {'p_send': sid, 'p_section': sec, 'p_ua': ua, 'p_ip': ip_hash})
            if section and dest:
                bump_link_click(section.get('campaign_id'), key, label, url)

        if not dest or not (str(dest).startswith('http://') or str(dest).startswith('https://')):
            dest = FALLBACK
        self.send_response(302)
        self.send_header('Location', dest)
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()

    def log_message(self, *a):
        pass
