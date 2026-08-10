/* ============================================
   CIELO HOUSE — Free resource pop up
   ============================================
   The e-book offered on the site. Which one, and the dates it runs, are set in
   the portal under Website, General, Pop Up. Nothing is decided here.

   It shows once per visit, between the from and to dates. The day after the
   end date it stops on its own, without anybody turning it off.
   ============================================ */
(function () {
  var SB = 'https://nkabuhbkuzcxajzrlenj.supabase.co';
  var SK = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5rYWJ1aGJrdXpjeGFqenJsZW5qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM0MzMwODQsImV4cCI6MjA4OTAwOTA4NH0.XsqejRlI7Cf_yu0Q6zOGAmBzWJKPeTZbIevjJ-3nWvo';
  var PORTAL = 'https://portal.cielohouse.com.au/api/ebooks/download';

  /* Today in Britt's time, so a pop up starts and finishes on the day she set. */
  function today() { return new Date(Date.now() + (10 * 3600 * 1000)).toISOString().slice(0, 10); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  var preview = /[?&]chpreview=/.test(location.search);

  function show(p) {
    if (document.getElementById('ch-resource-pop')) return;

    var wrap = document.createElement('div');
    wrap.id = 'ch-resource-pop';
    wrap.setAttribute('role', 'dialog');
    wrap.setAttribute('aria-modal', 'true');
    /* Britt's own "Popup, Free Resource" design, measurement for measurement.
       Nothing here is invented: the card, the image area, the type sizes, the
       rule, the field and the button are all as drawn. */
    wrap.innerHTML =
      '<style>' +
      '#ch-resource-pop{position:fixed;inset:0;z-index:99999;background:rgba(26,28,46,.55);' +
      'display:flex;align-items:center;justify-content:center;padding:40px;box-sizing:border-box;' +
      "font-family:'Poppins',system-ui,sans-serif}" +
      '#ch-resource-pop .card{position:relative;width:600px;max-width:100%;max-height:calc(100vh - 80px);' +
      'background:#FFFFFF;border-radius:2px;box-shadow:0 24px 64px rgba(42,46,125,0.22);' +
      'display:flex;flex-direction:column;overflow:auto}' +
      '#ch-resource-pop .x{position:absolute;top:20px;right:20px;z-index:3;width:40px;height:40px;' +
      'display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,0.92);' +
      'border:none;border-radius:0;color:#2A2E7D;font-size:20px;line-height:1;cursor:pointer;' +
      'transition:background 150ms ease}' +
      '#ch-resource-pop .x:hover{background:#FFFFFF}' +
      '#ch-resource-pop .pic{position:relative;height:380px;flex:none;background:#DCE8F7}' +
      '#ch-resource-pop .pic img{width:100%;height:100%;object-fit:cover;display:block}' +
      '#ch-resource-pop .body{flex:1;background:#2A2E7D;color:#FFFFFF;padding:56px 56px 48px;' +
      'display:flex;flex-direction:column}' +
      '#ch-resource-pop .eyebrow{font-size:14px;font-weight:700;letter-spacing:0.18em;' +
      'text-transform:uppercase;color:#648CC8}' +
      "#ch-resource-pop h1{font-family:'Bebas Neue',sans-serif;font-weight:400;font-size:64px;" +
      'line-height:0.98;letter-spacing:0.01em;text-transform:uppercase;margin:16px 0 0;text-wrap:balance}' +
      '#ch-resource-pop .rule{width:48px;height:3px;background:#648CC8;margin:24px 0 24px}' +
      '#ch-resource-pop p.sub{font-size:18px;line-height:1.5;margin:0;color:#DCE8F7;max-width:62ch}' +
      '#ch-resource-pop .spacer{flex:1;min-height:32px}' +
      '#ch-resource-pop .fields{display:flex;flex-direction:column;gap:16px}' +
      '#ch-resource-pop input{width:100%;box-sizing:border-box;padding:16px 18px;' +
      "font-family:'Poppins',sans-serif;font-size:16px;color:#2A2E7D;background:#FFFFFF;" +
      'border:1px solid #CBCBCB;border-radius:0;outline:none;transition:border-color 150ms ease}' +
      '#ch-resource-pop input:focus{border-color:#648CC8;border-width:2px;padding:15px 17px}' +
      "#ch-resource-pop button.go{width:100%;padding:18px 28px;font-family:'Poppins',sans-serif;" +
      'font-size:15px;font-weight:700;letter-spacing:0.18em;text-transform:uppercase;color:#2A2E7D;' +
      'background:#FFFFFF;border:2px solid #FFFFFF;border-radius:0;cursor:pointer;' +
      'transition:background 150ms ease,color 150ms ease}' +
      '#ch-resource-pop button.go:hover{background:#DCE8F7;border-color:#DCE8F7}' +
      '#ch-resource-pop button.go[disabled]{opacity:.6;cursor:default}' +
      '#ch-resource-pop .msg{font-size:18px;line-height:1.5;color:#DCE8F7;margin:0}' +
      '</style>' +
      '<div class="card">' +
        '<button class="x" type="button" aria-label="Close">&times;</button>' +
        '<div class="pic">' + (p.image ? '<img src="' + esc(p.image) + '" alt="">' : '') + '</div>' +
        '<div class="body">' +
          '<div class="eyebrow">Download for free</div>' +
          '<h1>' + esc(p.heading) + '</h1>' +
          '<div class="rule"></div>' +
          '<p class="sub">' + esc(p.sub) + '</p>' +
          '<div class="spacer"></div>' +
          '<div class="fields" id="ch-pop-form">' +
            '<input type="email" id="ch-pop-email" placeholder="Your email address" autocomplete="email">' +
            '<button class="go" type="button" id="ch-pop-go">Download Now</button>' +
          '</div>' +
        '</div>' +
      '</div>';

    document.body.appendChild(wrap);

    function close() {
      wrap.remove();
      try { sessionStorage.setItem('chResourceSeen', '1'); } catch (e) {}
      /* Opened as a preview from the portal, closing it closes the window and
         puts Britt back on Website, General. */
      if (preview) { try { window.close(); } catch (e) {} }
    }
    wrap.querySelector('.x').addEventListener('click', close);
    wrap.addEventListener('click', function (e) { if (e.target === wrap) close(); });
    document.addEventListener('keydown', function esckey(e) {
      if (e.key === 'Escape') { close(); document.removeEventListener('keydown', esckey); }
    });

    var go = wrap.querySelector('#ch-pop-go');
    go.addEventListener('click', function () {
      var em = String(wrap.querySelector('#ch-pop-email').value || '').trim();
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(em)) {
        wrap.querySelector('#ch-pop-email').focus();
        return;
      }
      go.disabled = true; go.textContent = 'Sending…';
      fetch(PORTAL, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: em, book: p.ebookName || p.heading, link: p.file || '' })
      }).then(function (r) { return r.json(); }).then(function (j) {
        if (!j || !j.ok) throw new Error((j && j.error) || 'it did not go');
        wrap.querySelector('#ch-pop-form').innerHTML =
          '<p class="msg">Check your email for your download.</p>';
      }).catch(function () {
        go.disabled = false; go.textContent = 'Download Now';
        wrap.querySelector('#ch-pop-form').insertAdjacentHTML('beforeend',
          '<p class="msg" style="margin-top:12px">That did not go through. Please try again shortly.</p>');
      });
    });
  }

  function start() {
    /* Once a visit is enough. The preview from the portal always shows it. */
    if (!preview) {
      try { if (sessionStorage.getItem('chResourceSeen')) return; } catch (e) {}
    }
    fetch(SB + '/rest/v1/site_chrome?id=eq.1&select=config',
      { headers: { apikey: SK, Authorization: 'Bearer ' + SK } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (rows) {
        var cfg = (rows && rows[0] && rows[0].config) || null;
        var p = cfg && cfg.popup;
        if (!p || !p.heading) return;
        if (!preview) {
          if (!p.enabled) return;
          var t = today();
          if (p.from && t < String(p.from).slice(0, 10)) return;
          if (p.to && t > String(p.to).slice(0, 10)) return;   // finished on its own
        }
        show(p);
      })
      .catch(function () {});
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
