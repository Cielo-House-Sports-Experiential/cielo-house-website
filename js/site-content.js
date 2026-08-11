/* ============================================================
   THE PAGE SHOWS WHAT THE PORTAL SAVED.

   Every Website page in the portal saves its words and pictures into a store of
   its own. Until 11.08.26 nothing on the public site read them, so publishing a
   page saved it and a visitor saw no change. This is what reads them.

   HOW A PAGE IS WIRED
     1. On <body>, say which store the page uses:
          <body data-ch-page="about_page">
     2. On any element, say which value fills it:
          data-ch="s1.heading"        the text of the element
          data-ch-para="s2.copy"      the text, blank lines becoming paragraphs
          data-ch-src="s2.image"      the src of an img or video
          data-ch-href="s5.pl"        the href of a link
     3. Include this file. Nothing else.

   THE STATIC HTML IS THE FALLBACK, NOT THE ENEMY.
   Whatever is already written in the page stays exactly as it is unless the
   store has something to put there. So a page with nothing saved yet looks the
   same as it does now, a search engine still sees real content, and somebody
   with no JavaScript still reads the page. An empty value in the store never
   blanks out what is on the page.
   ============================================================ */
(function () {
  var SB = 'https://nkabuhbkuzcxajzrlenj.supabase.co';
  var SK = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5rYWJ1aGJrdXpjeGFqenJsZW5qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM0MzMwODQsImV4cCI6MjA4OTAwOTA4NH0.XsqejRlI7Cf_yu0Q6zOGAmBzWJKPeTZbIevjJ-3nWvo';

  var table = document.body && document.body.getAttribute('data-ch-page');
  if (!table) return;

  /* "s3.i1.heading" out of the saved config. */
  function at(cfg, path) {
    var v = cfg;
    var parts = String(path || '').split('.');
    for (var i = 0; i < parts.length; i++) {
      if (v === null || typeof v !== 'object') return undefined;
      v = v[parts[i]];
    }
    return v;
  }

  /* A picture is stored the way the site refers to it, so a bare path is left
     alone and a full address is used as it is. */
  function url(v) {
    var s = String(v == null ? '' : v).trim();
    if (!s) return '';
    if (/^(https?:)?\/\//i.test(s) || s.charAt(0) === '/') return s;
    return s;
  }

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function apply(cfg) {
    if (!cfg || typeof cfg !== 'object') return;

    /* Some of what the portal holds is not words sitting on the page: the
       message shown after somebody subscribes, the address a form notifies, the
       booking link a widget opens. Those belong to the page's own script, so the
       whole config is handed over and an event is fired for anything waiting. */
    window.CH_PAGE = cfg;
    try { document.dispatchEvent(new CustomEvent('ch:content', { detail: cfg })); } catch (e) {}

    /* A heading is often styled in the page, with part of it in italics. The
       portal holds it as plain words. So if the saved words are the SAME as the
       ones already on the page, the page is left exactly as it is and keeps its
       styling. Only a heading that has actually been changed is replaced, and
       then it is replaced with the words that were saved. */
    function same(a, b) {
      return String(a || '').replace(/\s+/g, ' ').trim().toLowerCase()
          === String(b || '').replace(/\s+/g, ' ').trim().toLowerCase();
    }
    document.querySelectorAll('[data-ch]').forEach(function (el) {
      var v = at(cfg, el.getAttribute('data-ch'));
      if (v == null || v === '' || typeof v === 'object') return;
      if (same(v, el.textContent)) return;
      el.textContent = String(v);
    });

    document.querySelectorAll('[data-ch-para]').forEach(function (el) {
      var v = at(cfg, el.getAttribute('data-ch-para'));
      if (v == null || v === '' || typeof v === 'object') return;
      /* A blank line is a new paragraph, which is how it is typed in the portal. */
      el.innerHTML = String(v).split(/\n\s*\n/).map(function (p) {
        return '<p>' + esc(p.trim()).replace(/\n/g, '<br>') + '</p>';
      }).join('');
    });

    document.querySelectorAll('[data-ch-placeholder]').forEach(function (el) {
      var v = at(cfg, el.getAttribute('data-ch-placeholder'));
      if (v == null || v === '') return;
      el.setAttribute('placeholder', String(v));
    });

    document.querySelectorAll('[data-ch-src]').forEach(function (el) {
      var v = url(at(cfg, el.getAttribute('data-ch-src')));
      if (!v) return;
      el.setAttribute('src', v);
      if (el.tagName === 'VIDEO') { try { el.load(); } catch (e) {} }
    });

    /* An email button carries the address AND the subject, so its link is built
       from the two of them together. */
    document.querySelectorAll('[data-ch-mailto]').forEach(function (el) {
      var parts = String(el.getAttribute('data-ch-mailto') || '').split('|');
      var to = at(cfg, parts[0]);
      var subject = parts[1] ? at(cfg, parts[1]) : '';
      if (to == null || to === '') return;
      el.setAttribute('href', 'mailto:' + String(to)
        + (subject ? ('?subject=' + encodeURIComponent(String(subject))) : ''));
    });

    document.querySelectorAll('[data-ch-href]').forEach(function (el) {
      var v = at(cfg, el.getAttribute('data-ch-href'));
      if (v == null || v === '') return;
      el.setAttribute('href', String(v));
    });

    document.documentElement.setAttribute('data-ch-loaded', table);
  }

  fetch(SB + '/rest/v1/' + encodeURIComponent(table) + '?id=eq.1&select=config', {
    headers: { apikey: SK, Authorization: 'Bearer ' + SK }
  })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (rows) {
      if (Array.isArray(rows) && rows[0] && rows[0].config) apply(rows[0].config);
    })
    /* If it cannot be read the page simply keeps what is written in it. */
    .catch(function () {});
})();
