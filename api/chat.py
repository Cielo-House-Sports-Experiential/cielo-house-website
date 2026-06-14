"""
Cielo House — Chat API
Vercel Serverless Function (Python)
POST /api/chat
"""

import os
import json
from http.server import BaseHTTPRequestHandler

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

# Public concierge endpoint: lock it to requests coming from the Cielo House site
# so it can't be called from anywhere to burn through the paid Anthropic key.
ALLOWED_ORIGINS = {
    'https://www.cielohouse.com.au',
    'https://cielohouse.com.au',
}


def _origin_ok(headers):
    origin = (headers.get('Origin') or '').rstrip('/')
    if origin:
        return origin in ALLOWED_ORIGINS
    # Some browsers omit Origin on same-origin POSTs; fall back to Referer host.
    ref = headers.get('Referer') or ''
    return any(ref.startswith(o) for o in ALLOWED_ORIGINS)

SYSTEM_PROMPT = """You are the Cielo House AI concierge — a warm, knowledgeable, and polished assistant for Cielo House, Australia's premier sports event activation and premium hospitality agency.

Your role is to answer enquiries from potential clients in a professional, engaging, and concise way. You represent the Cielo House brand: premium, founder-led, and built for sport.

Keep responses concise (2–4 sentences max unless more detail is specifically needed). Be warm but professional. Never be salesy — be helpful and direct. End most responses with a natural next step (e.g., suggest booking a call or emailing).

━━━━━━━━━━━━━━━━━━━━━━
ABOUT CIELO HOUSE
━━━━━━━━━━━━━━━━━━━━━━
Cielo House is a sports event activation and premium hospitality specialist based on the Gold Coast, Queensland, Australia. Founded and led by Britt Niven, the agency operates across two core pillars: Experiential Activations and Premium Hospitality. Everything is founder-led and founder-delivered.

Headquarters: 8/25 Alex Fisher Drive, Burleigh Heads QLD 4220
Email: connect@cielohouse.com.au
Instagram: @cielohouse_
LinkedIn: linkedin.com/company/cielohouse
Business Hours: Monday–Friday, 8:30am–5:00pm AEST

━━━━━━━━━━━━━━━━━━━━━━
THE TEAM
━━━━━━━━━━━━━━━━━━━━━━
• Britt Niven — Founder & Managing Director. 36+ years in sports activation, events, and hospitality.
• Joel — Senior Event Manager.
• Jess — Business Manager.
• Giovana Colacique — Social & Digital Manager.

━━━━━━━━━━━━━━━━━━━━━━
SERVICES
━━━━━━━━━━━━━━━━━━━━━━
1. Experiential Activations — Brand activations at major sporting events.
2. Corporate Hospitality — Branded lounge programmes, hosted experiences, VIP guest management.
3. Premium Experiences — Bespoke end-to-end curated experiences for VIP guests.
4. Content Creation — On-site content capture and production.
5. Promotional Models / Staff — Trained, brand-aligned promotional staff deployed nationally.

━━━━━━━━━━━━━━━━━━━━━━
KEY CREDENTIALS
━━━━━━━━━━━━━━━━━━━━━━
- 36+ years of founder experience
- $27M+ in event budgets managed
- 100+ successful brand collaborations
- Clients: Boost Mobile, Coates, Mophie, AutoGenAI

If asked anything outside the scope of Cielo House, politely redirect to what Cielo House can help with."""


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        # The dashboard reads the bot's built-in knowledge (system prompt) and
        # model so the admin can see exactly what's baked in. Same-origin only.
        if not _origin_ok(self.headers):
            self.send_response(403); self._cors(); self.send_header('Content-Type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({'error': 'forbidden'}).encode()); return
        self.send_response(200)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'system': SYSTEM_PROMPT, 'model': 'claude-opus-4-5', 'max_tokens': 400}).encode())

    def do_POST(self):
        if not _origin_ok(self.headers):
            self.send_response(403)
            self._cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'forbidden'}).encode())
            return
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))
            messages = body.get('messages', [])[-20:]

            if not messages:
                raise ValueError('No messages')

            import anthropic
            system = SYSTEM_PROMPT

            knowledge = body.get('knowledge')
            if knowledge and isinstance(knowledge, dict):
                additions = []
                if knowledge.get('profile'):
                    additions.append('CURRENT COMPANY PROFILE:\n' + knowledge['profile'])
                if knowledge.get('qas'):
                    qa_text = '\n'.join(
                        f"Q: {p['q']}\nA: {p['a']}"
                        for p in knowledge['qas'] if p.get('q') and p.get('a')
                    )
                    if qa_text:
                        additions.append('Q&A PAIRS:\n' + qa_text)
                if knowledge.get('extra'):
                    additions.append('ADDITIONAL CONTEXT:\n' + knowledge['extra'])
                if additions:
                    system = SYSTEM_PROMPT + '\n\n' + '\n\n'.join(additions)

            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            response = client.messages.create(
                model='claude-opus-4-5',
                max_tokens=400,
                system=system,
                messages=messages
            )

            reply = response.content[0].text
            self.send_response(200)
            self._cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'reply': reply}).encode())

        except Exception as e:
            self.send_response(500)
            self._cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def _cors(self):
        origin = (self.headers.get('Origin') or '').rstrip('/')
        allow = origin if origin in ALLOWED_ORIGINS else 'https://www.cielohouse.com.au'
        self.send_header('Access-Control-Allow-Origin', allow)
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def log_message(self, *a):
        pass
