/* ============================================
   CIELO HOUSE — Event Calendar
   ============================================
   Events are managed via the Admin Dashboard.
   The calendar always displays up to 4 events,
   pulled from localStorage (ch_events).
   Edit events in the dashboard to update this page.
   ============================================ */

/* ---- Fallback events (used if dashboard has no data) ---- */
const FALLBACK_EVENTS = [
  {
    start: '2026-03-06', end: '2026-03-08',
    title: 'Formula 1 Qatar Airways Australian Grand Prix 2026',
    location: 'Melbourne, VIC',
    photo: 'images/events-calendar/formula-1-australian-grand-prix/GP26-79.jpg',
  },
  {
    start: '2026-03-07', end: '2026-03-08',
    title: 'Australian Boardriders Battle',
    location: 'Gold Coast, QLD',
    photo: 'images/events-calendar/australian-boardriders-battle/BoardRiders26-97.jpg',
  },
  {
    start: '2026-04-01', end: '2026-04-11',
    title: 'WSL Rip Curl Pro Bells Beach',
    location: 'Melbourne, VIC',
    photo: 'images/events-calendar/wsl-rip-curl-bells-beach/wsl-bells-beach.jpg',
  },
  {
    start: '2026-10-24', end: '2026-10-26',
    title: 'Boost Mobile Gold Coast 500',
    location: 'Gold Coast, QLD',
    photo: 'images/events-calendar/boost-mobile-gold-coast-500/BoostGC500-21.jpg',
  },
];

/* ---- Format date: "2026-03-06" → "06.03" ---- */
function fmtDate(str) {
  if (!str) return '';
  const parts = str.split('-');
  if (parts.length < 3) return str;
  return parts[2] + '.' + parts[1];
}

/* ---- Build display dates string ---- */
function buildDates(start, end) {
  if (!start) return '';
  const s = fmtDate(start);
  if (!end || end === start) return s;
  return s + ' - ' + fmtDate(end);
}

/* ---- Supabase (live source of truth — same anon key the rest of the site uses) ---- */
var EVENTS_SB = 'https://nkabuhbkuzcxajzrlenj.supabase.co';
var EVENTS_SK = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5rYWJ1aGJrdXpjeGFqenJsZW5qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM0MzMwODQsImV4cCI6MjA4OTAwOTA4NH0.XsqejRlI7Cf_yu0Q6zOGAmBzWJKPeTZbIevjJ-3nWvo';

/* ---- Load events from Supabase (same on every device), max 4 ---- */
function loadEvents() {
  fetch(EVENTS_SB + '/rest/v1/site_events?select=title,location,start_date,end_date,photo&order=start_date.asc&limit=4', { headers: { apikey: EVENTS_SK, Authorization: 'Bearer ' + EVENTS_SK } })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (rows) {
      if (!rows || !rows.length) { renderEvents(FALLBACK_EVENTS.slice(0, 4)); return; }
      renderEvents(rows.map(function (e) {
        return { title: e.title, location: e.location, start: e.start_date, end: e.end_date, photo: e.photo };
      }));
    })
    .catch(function () { renderEvents(FALLBACK_EVENTS.slice(0, 4)); });
}

/* ---- Render ---- */
function renderEvents(events) {
  var grid = document.getElementById('events-grid');
  if (!grid) return;
  if (!events || !events.length) events = FALLBACK_EVENTS.slice(0, 4);
  grid.setAttribute('data-count', events.length);

  grid.innerHTML = events.map(function(ev, i) {
    var name     = ev.title    || ev.name     || '';
    var location = ev.location || '';
    var image    = ev.photo    || ev.image    || '';
    var dates    = buildDates(ev.start, ev.end) || ev.dates || '';

    return [
      '<div class="event-card" role="listitem" aria-label="' + name + '">',
        '<div class="event-card__img-wrap">',
          '<img src="' + image + '" alt="' + name + '" class="event-card__img" loading="' + (i === 0 ? 'eager' : 'lazy') + '" />',
          '<div class="event-card__overlay"></div>',
        '</div>',
        '<div class="event-card__body">',
          '<span class="event-card__dates">' + dates + '</span>',
          '<h3 class="event-card__name">' + name + '</h3>',
          '<span class="event-card__location">',
            '<svg viewBox="0 0 16 16" fill="none" width="12" height="12" aria-hidden="true">',
              '<path d="M8 1.5A4.5 4.5 0 0 1 12.5 6c0 3.5-4.5 8.5-4.5 8.5S3.5 9.5 3.5 6A4.5 4.5 0 0 1 8 1.5z" stroke="currentColor" stroke-width="1.2"/>',
              '<circle cx="8" cy="6" r="1.5" stroke="currentColor" stroke-width="1.2"/>',
            '</svg>',
            location,
          '</span>',
        '</div>',
      '</div>',
    ].join('');
  }).join('');
}

document.addEventListener('DOMContentLoaded', loadEvents);
