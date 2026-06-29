"""
Cielo House — AI Answer Visibility runner (server-side).
POST /api/ai-visibility-run

Replaces the old in-browser checks (which broke on CORS, per-browser keys and
constant model-name churn). Reads the AI keys already saved in
dashboard_secrets, asks each model the AI_QUERIES, records whether "Cielo House"
is mentioned, and stores results in ai_visibility_results. The dashboard just
reads that table, so every device (and Gio) sees the same data.

Auth: same-origin (the dashboard button) OR ?token=<RUN_TOKEN> (for cron/tests).
Secrets never leave the server.
"""
import os, json, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler

SB = os.environ.get('SUPABASE_URL', 'https://nkabuhbkuzcxajzrlenj.supabase.co')
SR = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
RUN_TOKEN = 'cielo-aivis-run-2026-9f3ac71b'

ALLOWED_ORIGINS = {'https://www.cielohouse.com.au', 'https://cielohouse.com.au'}

AI_QUERIES = [
    'best sports activation agency in Australia',
    'experiential marketing agency Gold Coast Australia',
    'corporate hospitality sports events Australia',
    'sports sponsorship activation Gold Coast',
    'brand activation agency Australia events',
    'VIP experiences Supercars F1 Australia',
    'promotional models brand ambassadors Australia sports',
    'experiential marketing agency Brisbane Gold Coast',
    'sports event activation company Australia',
    'hospitality packages Formula 1 Australian Grand Prix',
    'top experiential marketing agencies in Australia',
    'corporate hospitality providers Australian Grand Prix',
    'brand activation companies Gold Coast',
    'event marketing agency Queensland',
    'sports marketing agency Australia',
    'who runs brand activations at Supercars events',
    'premium corporate hospitality Supercars Gold Coast 500',
    'experiential agency for sponsorship activation Australia',
    'best agency for event activations in Queensland',
    'corporate hospitality Formula 1 Melbourne',
    'brand experience agency Australia',
    'activation agency for sporting events Australia',
    'companies that provide brand ambassadors for events Australia',
    'VIP hospitality packages Supercars',
    'experiential marketing companies Brisbane',
    'sports hospitality agency Australia',
    'event staffing and promotional models Gold Coast',
    'agencies that do brand activations at the F1 Grand Prix',
    'corporate event management sports Australia',
    'experiential marketing for brands at Australian sporting events',
    'who to hire for sponsorship activation in Australia',
    'best brand activation agency for sporting events',
    'luxury corporate hospitality Australian sport',
    'experiential marketing agency for automotive brands Australia',
    'event activation specialists Gold Coast Queensland',
    'WSL surfing event hospitality and activation Australia',
    'agencies for VIP experiences at motorsport events Australia',
    'brand activation and experiential agency Sydney Melbourne',
    'corporate hospitality and guest management sporting events Australia',
    'full service experiential marketing agency Australia',
]

SUFFIX = (' (At the very end of your answer, on a new line, write '
          'MENTIONS_CIELO_HOUSE: YES if your answer refers to the agency '
          '"Cielo House", otherwise MENTIONS_CIELO_HOUSE: NO.)')


def _sb_headers():
    return {'apikey': SR, 'Authorization': 'Bearer ' + SR, 'Content-Type': 'application/json'}


def _http(url, method='POST', headers=None, body=None, timeout=45):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode().strip()
        return json.loads(raw) if raw else None


def _err_text(e):
    if isinstance(e, urllib.error.HTTPError):
        try:
            body = json.loads(e.read().decode())
            msg = (body.get('error') or {})
            if isinstance(msg, dict):
                return (msg.get('message') or json.dumps(msg))[:200]
            return str(msg)[:200]
        except Exception:
            return 'HTTP %s' % e.code
    return str(e)[:200]


def get_keys():
    rows = _http(SB + '/rest/v1/dashboard_secrets?id=eq.main&select=vals',
                 method='GET', headers=_sb_headers(), timeout=10)
    vals = (rows[0]['vals'] if rows else {}) or {}
    return {
        'gemini': vals.get('ch_key_gemini', ''),
        'openai': vals.get('ch_key_openai', ''),
        'perplexity': vals.get('ch_key_perplexity', ''),
    }


def current_gemini_model(key):
    """Ask Google which flash model is live, so a retired name never breaks us."""
    try:
        data = _http('https://generativelanguage.googleapis.com/v1beta/models?key=' + key,
                     method='GET', timeout=15)
        names = []
        for m in data.get('models', []):
            nm = m.get('name', '').split('/')[-1]
            methods = m.get('supportedGenerationMethods') or []
            if 'generateContent' in methods and 'flash' in nm.lower() \
                    and 'vision' not in nm.lower() and 'thinking' not in nm.lower():
                names.append(nm)
        # Prefer a stable (non -exp/-preview) highest version flash model.
        stable = [n for n in names if 'exp' not in n and 'preview' not in n]
        pick = sorted(stable or names, reverse=True)
        return pick[0] if pick else 'gemini-flash-latest'
    except Exception:
        return 'gemini-flash-latest'


def detect(text):
    lc = (text or '').lower()
    return ('cielo house' in lc) or ('mentions_cielo_house: yes' in lc)


def ask_gemini(key, model, q):
    url = ('https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s'
           % (model, key))
    body = {'contents': [{'parts': [{'text': q + SUFFIX}]}],
            'generationConfig': {'maxOutputTokens': 250, 'temperature': 0.3}}
    j = _http(url, headers={'Content-Type': 'application/json'}, body=body)
    return j['candidates'][0]['content']['parts'][0]['text']


def ask_openai(key, q):
    body = {'model': 'gpt-4o-mini', 'messages': [{'role': 'user', 'content': q + SUFFIX}],
            'max_tokens': 250, 'temperature': 0.3}
    j = _http('https://api.openai.com/v1/chat/completions',
              headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'},
              body=body)
    return j['choices'][0]['message']['content']


def ask_perplexity(key, q):
    body = {'model': 'sonar', 'messages': [{'role': 'user', 'content': q + SUFFIX}],
            'max_tokens': 250, 'temperature': 0.3}
    j = _http('https://api.perplexity.ai/chat/completions',
              headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'},
              body=body)
    return j['choices'][0]['message']['content']


def run_one(model_name, fn, q):
    try:
        text = fn(q)
        return {'model': model_name, 'query': q, 'mentioned': detect(text),
                'snippet': (text or '').strip()[:200], 'error': ''}
    except Exception as e:
        return {'model': model_name, 'query': q, 'mentioned': False,
                'snippet': '', 'error': _err_text(e)}


def run_all():
    keys = get_keys()
    gem_model = current_gemini_model(keys['gemini']) if keys['gemini'] else None
    tasks = []
    for q in AI_QUERIES:
        if keys['gemini']:
            tasks.append(('gemini', lambda q=q: ask_gemini(keys['gemini'], gem_model, q), q))
        if keys['openai']:
            tasks.append(('chatgpt', lambda q=q: ask_openai(keys['openai'], q), q))
        if keys['perplexity']:
            tasks.append(('perplexity', lambda q=q: ask_perplexity(keys['perplexity'], q), q))

    results = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        futs = [ex.submit(run_one, m, fn, q) for (m, fn, q) in tasks]
        for f in futs:
            results.append(f.result())

    run_id = str(int(time.time()))
    rows = [{'run_id': run_id, 'model': r['model'], 'query': r['query'],
             'mentioned': r['mentioned'], 'snippet': r['snippet'], 'error': r['error']}
            for r in results]

    # Replace previous snapshot with this run.
    try:
        _http(SB + '/rest/v1/ai_visibility_results?id=gt.0', method='DELETE',
              headers=dict(_sb_headers(), **{'Prefer': 'return=minimal'}), timeout=20)
    except Exception:
        pass
    # Insert in chunks to stay under payload limits.
    for i in range(0, len(rows), 100):
        _http(SB + '/rest/v1/ai_visibility_results', method='POST',
              headers=dict(_sb_headers(), **{'Prefer': 'return=minimal'}),
              body=rows[i:i + 100], timeout=30)

    summary = {'run_id': run_id, 'gemini_model': gem_model,
               'models': {}, 'total_queries': len(AI_QUERIES)}
    for m in ('gemini', 'chatgpt', 'perplexity'):
        mr = [r for r in results if r['model'] == m]
        if mr:
            summary['models'][m] = {
                'mentioned': sum(1 for r in mr if r['mentioned']),
                'queries': len(mr),
                'errors': sum(1 for r in mr if r['error']),
                'sample_error': next((r['error'] for r in mr if r['error']), ''),
            }
    return summary


class handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        payload = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(payload)

    def _authed(self):
        origin = (self.headers.get('Origin') or '').rstrip('/')
        if origin and origin in ALLOWED_ORIGINS:
            return True
        ref = self.headers.get('Referer') or ''
        if any(ref.startswith(o) for o in ALLOWED_ORIGINS):
            return True
        # token in query string (cron / server-to-server)
        q = (self.path.split('?', 1)[1] if '?' in self.path else '')
        return ('token=' + RUN_TOKEN) in q

    def do_POST(self):
        if not SR:
            return self._send(500, {'error': 'SUPABASE_SERVICE_ROLE_KEY not set on the server'})
        if not self._authed():
            return self._send(403, {'error': 'forbidden'})
        try:
            summary = run_all()
            return self._send(200, {'ok': True, **summary})
        except Exception as e:
            return self._send(500, {'error': _err_text(e)})

    def do_GET(self):
        # convenience: allow a token-authed GET to trigger a run too
        self.do_POST()
