/**
 * Cielo House — Visitor Tracking & Cookie Consent
 * Writes to localStorage['ch_activity_log'] (shared across same-origin pages)
 * Dashboard reads this to show real visitor journeys.
 */
(function () {
  'use strict';

  var CONSENT_KEY = 'ch_tracking_consent';
  var LOG_KEY     = 'ch_activity_log';
  var MAX_ENTRIES = 500;

  /* ── Helpers ─────────────────────────────────────────────────── */
  function uuid() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      var r = Math.random() * 16 | 0;
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
  }

  function getDevice() {
    var ua = navigator.userAgent;
    if (/Mobi|Android/i.test(ua)) return 'Mobile';
    if (/Tablet|iPad/i.test(ua)) return 'Tablet';
    return 'Desktop';
  }

  function getSource() {
    var ref = document.referrer;
    if (!ref) return 'Direct';
    if (/google\./i.test(ref))   return 'Google';
    if (/bing\./i.test(ref))     return 'Bing';
    if (/linkedin\./i.test(ref)) return 'LinkedIn';
    if (/facebook\.|fb\./i.test(ref)) return 'Facebook';
    if (/instagram\./i.test(ref)) return 'Instagram';
    try { return new URL(ref).hostname.replace(/^www\./, ''); } catch(e) { return ref; }
  }

  function getPageLabel() {
    var path = location.pathname.replace(/\/$/, '') || '/';
    var map = {
      '/':                        'Home',
      '/index':                   'Home',
      '/index.html':              'Home',
      '/home':                    'Home',
      '/home.html':               'Home',
      '/about':                   'About',
      '/about.html':              'About',
      '/services':                'Services',
      '/services.html':           'Services',
      '/work':                    'Work / Portfolio',
      '/work.html':               'Work / Portfolio',
      '/blog':                    'Blog',
      '/blog.html':               'Blog',
      '/contact':                 'Contact',
      '/contact.html':            'Contact',
      '/privacy':                 'Privacy Policy',
      '/privacy.html':            'Privacy Policy',
      '/terms':                   'Terms',
      '/terms.html':              'Terms'
    };
    // services sub-pages
    if (/services\/brand-activation/i.test(path)) return 'Service: Brand Activations';
    if (/services\/corporate-hospitality/i.test(path)) return 'Service: Corporate Hospitality';
    if (/services\/experiential/i.test(path)) return 'Service: Experiential';
    if (/services\/premium/i.test(path)) return 'Service: Premium Experiences';
    if (/services\/content/i.test(path)) return 'Service: Content Creation';
    // blog posts
    if (/blog\//i.test(path)) {
      var slug = path.split('/').pop().replace(/\.html$/, '').replace(/-/g, ' ');
      return 'Blog: ' + slug.replace(/\b\w/g, function(c){return c.toUpperCase();});
    }
    return map[path] || map[path + '.html'] || document.title || path;
  }

  function readLog() {
    try { return JSON.parse(localStorage.getItem(LOG_KEY) || '[]'); } catch(e) { return []; }
  }

  function writeLog(log) {
    // Keep newest MAX_ENTRIES only
    if (log.length > MAX_ENTRIES) log = log.slice(log.length - MAX_ENTRIES);
    try { localStorage.setItem(LOG_KEY, JSON.stringify(log)); } catch(e) {}
  }

  function pushEntry(entry) {
    var log = readLog();
    log.push(entry);
    writeLog(log);
  }

  /* ── IDs ─────────────────────────────────────────────────────── */
  // Visitor ID — persists across sessions (localStorage)
  var visitorId = localStorage.getItem('ch_visitor_id');
  if (!visitorId) { visitorId = uuid(); localStorage.setItem('ch_visitor_id', visitorId); }

  // Session ID — one per browser session (sessionStorage)
  var sessionId = sessionStorage.getItem('ch_session_id');
  if (!sessionId) { sessionId = uuid(); sessionStorage.setItem('ch_session_id', sessionId); }

  /* ── Track page view ─────────────────────────────────────────── */
  function trackPageView() {
    var entry = {
      id:        uuid(),
      type:      'page_view',
      page:      getPageLabel(),
      path:      location.pathname,
      visitorId: visitorId,
      sessionId: sessionId,
      device:    getDevice(),
      source:    getSource(),
      time:      new Date().toISOString(),
      duration:  null   // filled on unload
    };
    // Store ref so we can update duration
    sessionStorage.setItem('ch_current_entry_id', entry.id);
    sessionStorage.setItem('ch_page_start', Date.now().toString());
    pushEntry(entry);
  }

  /* ── Update duration on leave ────────────────────────────────── */
  function updateDuration() {
    var entryId = sessionStorage.getItem('ch_current_entry_id');
    var start   = parseInt(sessionStorage.getItem('ch_page_start') || '0');
    if (!entryId || !start) return;
    var secs = Math.round((Date.now() - start) / 1000);
    if (secs < 1) return;
    var log = readLog();
    for (var i = log.length - 1; i >= 0; i--) {
      if (log[i].id === entryId) { log[i].duration = secs; break; }
    }
    writeLog(log);
  }

  window.addEventListener('pagehide', updateDuration);
  window.addEventListener('beforeunload', updateDuration);

  /* ── Track CTA clicks ────────────────────────────────────────── */
  function trackCTA(label) {
    pushEntry({
      id:        uuid(),
      type:      'cta_click',
      label:     label,
      page:      getPageLabel(),
      path:      location.pathname,
      visitorId: visitorId,
      sessionId: sessionId,
      device:    getDevice(),
      source:    getSource(),
      time:      new Date().toISOString()
    });
  }

  // Auto-instrument common CTA patterns
  document.addEventListener('click', function (e) {
    var el = e.target.closest('a,button');
    if (!el) return;
    var text = (el.innerText || el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 60);
    var href = el.getAttribute('href') || '';
    // Booking / briefing buttons
    if (/book|brief|contact|enquir|get.in.touch|call|start/i.test(text + href)) {
      trackCTA(text || 'CTA Button');
    }
    // Phone / email links
    if (/^tel:|^mailto:/.test(href)) {
      trackCTA((href.startsWith('tel:') ? '📞 ' : '✉ ') + href.replace(/^tel:|^mailto:/, ''));
    }
  });

  /* ── Keep-alive heartbeat (for "live now") ───────────────────── */
  function heartbeat() {
    try {
      var beats = JSON.parse(localStorage.getItem('ch_heartbeats') || '{}');
      beats[sessionId] = { visitorId: visitorId, page: getPageLabel(), path: location.pathname, device: getDevice(), time: new Date().toISOString() };
      // Clean beats older than 10 min
      var cutoff = Date.now() - 10 * 60 * 1000;
      Object.keys(beats).forEach(function(k) {
        if (new Date(beats[k].time).getTime() < cutoff) delete beats[k];
      });
      localStorage.setItem('ch_heartbeats', JSON.stringify(beats));
    } catch(e) {}
  }

  /* ── Consent check ───────────────────────────────────────────── */
  function hasConsent() {
    return localStorage.getItem(CONSENT_KEY) === 'yes';
  }

  function grantConsent() {
    localStorage.setItem(CONSENT_KEY, 'yes');
    hideBanner();
    startTracking();
  }

  function denyConsent() {
    localStorage.setItem(CONSENT_KEY, 'no');
    hideBanner();
  }

  function startTracking() {
    trackPageView();
    heartbeat();
    setInterval(heartbeat, 30000); // every 30s
  }

  /* ── Cookie banner ───────────────────────────────────────────── */
  function showBanner() {
    if (document.getElementById('ch-cookie-banner')) return;

    var banner = document.createElement('div');
    banner.id = 'ch-cookie-banner';
    banner.style.cssText = [
      'position:fixed','bottom:0','left:0','right:0','z-index:99999',
      'background:#1a1f52','color:#fff','font-family:Poppins,sans-serif',
      'font-size:0.85rem','padding:1rem 1.5rem',
      'display:flex','align-items:center','gap:1rem','flex-wrap:wrap',
      'box-shadow:0 -4px 20px rgba(0,0,0,0.3)'
    ].join(';');

    banner.innerHTML =
      '<div style="flex:1;min-width:200px;line-height:1.5;">' +
        'We use cookies to help us improve your experience. ' +
        '<a href="/privacy.html" style="color:#93b4e8;text-decoration:underline;">Privacy Policy</a>' +
      '</div>' +
      '<div style="display:flex;gap:0.5rem;flex-shrink:0;">' +
        '<button id="ch-cookie-deny" style="background:transparent;border:1.5px solid rgba(255,255,255,0.35);color:#ccc;padding:0.5rem 1rem;border-radius:6px;cursor:pointer;font-family:Poppins,sans-serif;font-size:0.82rem;font-weight:600;">Decline</button>' +
        '<button id="ch-cookie-accept" style="background:#668DC6;border:none;color:#fff;padding:0.5rem 1.25rem;border-radius:6px;cursor:pointer;font-family:Poppins,sans-serif;font-size:0.82rem;font-weight:700;">Accept All</button>' +
      '</div>';

    document.body.appendChild(banner);

    document.getElementById('ch-cookie-accept').addEventListener('click', grantConsent);
    document.getElementById('ch-cookie-deny').addEventListener('click', denyConsent);
  }

  function hideBanner() {
    var b = document.getElementById('ch-cookie-banner');
    if (b) b.remove();
  }

  /* ── Entry point ─────────────────────────────────────────────── */
  function init() {
    var consent = localStorage.getItem(CONSENT_KEY);
    if (consent === 'yes') {
      startTracking();
    } else if (consent === 'no') {
      // Respect the "no" — don't show banner again, don't track
    } else {
      // First visit — show banner
      // Show after a tiny delay so page renders first
      setTimeout(showBanner, 800);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
