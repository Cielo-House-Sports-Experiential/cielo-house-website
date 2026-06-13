/* ============================================================
   Cielo House — Case study detail renderer
   Reads the case study for THIS page from Supabase (case_studies)
   and overrides the static HTML. The static content stays in the
   page as the SEO / no-JS fallback. Same Supabase + anon key the
   blog uses — separate table, no localStorage.
   Slug is taken from the page filename (e.g. boost-mobile-gold-coast-500).
   ============================================================ */
(function () {
  var SB = 'https://nkabuhbkuzcxajzrlenj.supabase.co';
  var SK = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5rYWJ1aGJrdXpjeGFqenJsZW5qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM0MzMwODQsImV4cCI6MjA4OTAwOTA4NH0.XsqejRlI7Cf_yu0Q6zOGAmBzWJKPeTZbIevjJ-3nWvo';

  var slug = (location.pathname.split('/').pop() || '').replace(/\.html$/, '');
  if (!slug) return;

  function setText(id, val) {
    var el = document.getElementById(id);
    if (el && val != null && val !== '') el.textContent = val;
  }
  function setHTML(id, val) {
    var el = document.getElementById(id);
    if (el && val != null && val !== '') el.innerHTML = val;
  }
  // Image paths are stored root-relative (images/...) for work.html. Detail
  // pages live one level deep in /work, so prefix ../ unless already absolute.
  function resolveImg(p) {
    if (!p) return p;
    if (/^(https?:|\/|\.\.\/|data:)/.test(p)) return p;
    return '../' + p;
  }

  fetch(SB + '/rest/v1/case_studies?slug=eq.' + encodeURIComponent(slug) + '&select=*', { headers: { apikey: SK, Authorization: 'Bearer ' + SK } })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (rows) {
      if (!rows || !rows.length) return; // keep static fallback
      var d = rows[0];

      if (d.meta_title) document.title = d.meta_title;

      setText('cs-hero-tag', d.hero_tag);
      setText('cs-title', d.title);

      // Hero meta — line separated
      setText('cs-client', d.client);
      setText('cs-event', d.event);
      setText('cs-event-type', d.event_type);

      var hero = document.getElementById('cs-hero-image');
      if (hero && d.hero_image) { hero.src = resolveImg(d.hero_image); if (d.hero_image_alt) hero.alt = d.hero_image_alt; }

      setHTML('cs-lead', d.lead);
      setHTML('cs-brief', d.brief);
      setHTML('cs-delivered', d.delivered);
      setText('cs-quote', d.quote);
      setText('cs-attribution', d.attribution);

      var stats = Array.isArray(d.stats) ? d.stats : [];
      for (var i = 0; i < 3; i++) {
        var s = stats[i] || {};
        setText('cs-stat' + (i + 1) + 'n', s.n);
        setText('cs-stat' + (i + 1) + 'd', s.d);
      }

      // Sidebar meta-card
      setText('cs-meta-client', d.client);
      setText('cs-meta-event', d.event);
      setText('cs-meta-location', d.meta_location);
      setText('cs-meta-year', d.meta_year);
      setText('cs-meta-services', d.meta_services);

      // Bottom CTA
      setText('cs-cta-title', d.cta_title);
      setText('cs-cta-body', d.cta_body);
    })
    .catch(function () {});
})();
