#!/usr/bin/env python3
"""
Cielo House — Chat API Server
Serves static files on port 8000 AND handles POST /api/chat with Claude AI.

Usage:
  1. Set your Anthropic API key below (or as env var ANTHROPIC_API_KEY)
  2. Run:  python3 chat_server.py
  3. Open: http://localhost:8000
"""

import os
import json
import http.server
import anthropic

# ── API Key ──────────────────────────────────────────────────────────────────
# Set here directly, or export ANTHROPIC_API_KEY=sk-ant-... before running
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', 'YOUR_API_KEY_HERE')

# ── System Prompt ─────────────────────────────────────────────────────────────
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
• Britt Niven — Founder & Managing Director. 36+ years in sports activation, events, and hospitality. Born in Sydney. Personally present at every event. Dream event: F1 Las Vegas.
• Joel — Senior Event Manager. From Rockhampton. Dream event: Olympics.
• Jess — Business Manager. Gold Coast local. Dream event: Victoria's Secret Show.
• Giovana Colacique — Social & Digital Manager. Originally from Brazil. Dream event: WSL.

━━━━━━━━━━━━━━━━━━━━━━
THE TWO PILLARS
━━━━━━━━━━━━━━━━━━━━━━

PILLAR 1 — EXPERIENTIAL ACTIVATIONS
From concept through to bump-out. Cielo House designs and delivers brand experiences at major Australian sporting properties.
- Race day activations and fan engagement zones
- Sponsor inventory build-out
- On-site content capture
- Activation concept and design
- Brand ambassador and promotional staff integration

PILLAR 2 — PREMIUM HOSPITALITY
Branded lounges, hosted programmes, talent integration, and guest experiences built for the sport environment. Planned in reverse from departure so the production standard holds from the kerb to the final moment.
- Branded lounge concept and fit-out
- Guest experience sequence design
- Talent and host integration
- Crew management and onsite service standards
- VIP and key relationship management

━━━━━━━━━━━━━━━━━━━━━━
ALL SERVICES (5 TOTAL)
━━━━━━━━━━━━━━━━━━━━━━
1. Experiential Activations — Brand activations at major sporting events. Fan zones, sponsor build-outs, content capture.
2. Corporate Hospitality — Branded lounge programmes, hosted experiences, VIP guest management at sporting events.
3. Premium Experiences — Bespoke end-to-end curated experiences for VIP guests, brand partners, and key relationships. Multi-day itinerary management, partner and influencer experiences.
4. Content Creation — On-site content capture and production. Social-first distribution, maximum brand reach, photography and video.
5. Promotional Models / Staff — Trained, brand-aligned promotional staff and brand ambassadors deployed nationally. Professional, always on-brief.

━━━━━━━━━━━━━━━━━━━━━━
PROVEN CLIENTS & EVENTS
━━━━━━━━━━━━━━━━━━━━━━
- Boost Mobile — Gold Coast 500 (Supercars Championship)
- Coates — F1 Australian Grand Prix (Melbourne); Supercars Championship (multiple rounds)
- Mophie — Surfing activations (WSL events)
- AutoGenAI PTY LTD — Events function rebuild

Events regularly worked at:
- Formula 1 Australian Grand Prix (Melbourne, March)
- Gold Coast 500 / Boost Mobile Gold Coast 500 (Supercars, Gold Coast, October)
- WSL Rip Curl Pro Bells Beach (April)
- Australian Boardriders Battle (Gold Coast)
- Various Supercars Championship rounds across Australia
- Major Gold Coast and Queensland sporting properties

━━━━━━━━━━━━━━━━━━━━━━
KEY CREDENTIALS
━━━━━━━━━━━━━━━━━━━━━━
- 36+ years of founder experience in the sport environment
- $27M+ in event budgets managed
- 100+ successful brand collaborations
- Gold Coast based — strong relationships with Gold Coast sporting properties, venues, and event organisers
- Not a full-service agency: specialist model only (protects the standard)
- Britt personally on the ground at every event

━━━━━━━━━━━━━━━━━━━━━━
THE BRIEF PROCESS
━━━━━━━━━━━━━━━━━━━━━━
The process starts with a brief. Clients bring:
1. The event or events they are activating at
2. The activation type: brand zone, hospitality, or both
3. A budget bracket (even a rough one)
4. The outcome they are trying to achieve for the brand

The first conversation is a brief discussion, not a sales call. Clients leave it knowing whether Cielo House is the right fit and what delivery will take.

━━━━━━━━━━━━━━━━━━━━━━
WHAT CIELO HOUSE DOES NOT DO
━━━━━━━━━━━━━━━━━━━━━━
- Not a full-service agency
- Does not take on work outside sport activation and premium hospitality
- If a brief doesn't belong to one of the two pillars, Cielo House will say so honestly

━━━━━━━━━━━━━━━━━━━━━━
TONE GUIDE
━━━━━━━━━━━━━━━━━━━━━━
- Professional, warm, and direct
- No jargon or buzzwords
- Confident without being arrogant
- Reflect the premium, founder-led nature of the brand
- Always be honest — if something is outside scope, say so
- Suggest next steps: Book a Discovery Call or email connect@cielohouse.com.au

If asked anything outside the scope of Cielo House (e.g., unrelated topics), politely redirect to what Cielo House can help with."""

# ── Handler ───────────────────────────────────────────────────────────────────
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path != '/api/chat':
            self.send_error(404)
            return

        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)

        try:
            data = json.loads(body)
            messages = data.get('messages', [])

            # Validate
            if not messages or not isinstance(messages, list):
                raise ValueError('No messages')

            # Trim to last 20 messages to keep context manageable
            messages = messages[-20:]

            # Build dynamic system prompt — inject dashboard knowledge base if provided
            system = SYSTEM_PROMPT
            knowledge = data.get('knowledge')
            if knowledge and isinstance(knowledge, dict):
                additions = []
                if knowledge.get('profile'):
                    additions.append('━━━━━━━━━━━━━━━━━━━━━━\nCURRENT COMPANY PROFILE (admin-updated)\n━━━━━━━━━━━━━━━━━━━━━━\n' + knowledge['profile'])
                if knowledge.get('qas'):
                    qa_text = '\n'.join(
                        f"Q: {pair['q']}\nA: {pair['a']}"
                        for pair in knowledge['qas']
                        if pair.get('q') and pair.get('a')
                    )
                    if qa_text:
                        additions.append('━━━━━━━━━━━━━━━━━━━━━━\nCURATED Q&A PAIRS (admin-provided)\n━━━━━━━━━━━━━━━━━━━━━━\n' + qa_text)
                if knowledge.get('extra'):
                    additions.append('━━━━━━━━━━━━━━━━━━━━━━\nADDITIONAL INSTRUCTIONS (admin-provided)\n━━━━━━━━━━━━━━━━━━━━━━\n' + knowledge['extra'])
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
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'reply': reply}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def log_message(self, fmt, *args):
        # Only log API calls, not static files
        first = str(args[0]) if args else ''
        if '/api/' in first:
            print(f'[CHAT] {first} → {args[1] if len(args) > 1 else ""}')


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    if ANTHROPIC_API_KEY == 'YOUR_API_KEY_HERE':
        print('⚠️  No API key set. Export ANTHROPIC_API_KEY or edit chat_server.py')
    else:
        print('✓  Anthropic API key loaded')

    port = 8000
    print(f'✓  Cielo House server running → http://localhost:{port}')
    print('   Press Ctrl+C to stop\n')

    import socketserver
    class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True
        daemon_threads = True
    with ThreadedServer(('', port), Handler) as httpd:
        httpd.serve_forever()
