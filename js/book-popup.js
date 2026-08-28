/* BOOK A BRIEFING CALL, WITHOUT LEAVING THE PAGE.
   Every "Schedule a Briefing Call" on the site points at the contact page's
   discovery-call section. They all now open our own booking page over the top
   of whatever page you are on instead.

   It is written once here rather than on each page, so the seven of them can
   never drift apart.

   display is set in this stylesheet and NOT on the element. An inline display
   beats a stylesheet rule for a hidden element, and that is exactly what put an
   empty white box over the live contact page on 28.08.26. */
(function () {
  var URL_BOOK = '/book/briefing-call';
  var box = null, frame = null;

  function build() {
    if (box) return;
    var css = document.createElement('style');
    css.textContent =
      '#chBookBox{position:fixed;inset:0;background:rgba(43,49,123,.6);z-index:2000;'
      + 'display:flex;align-items:flex-start;justify-content:center;padding:3vh 1rem;}'
      + '#chBookBox[hidden]{display:none;}'
      + '#chBookCard{position:relative;width:min(860px,94vw);height:auto;max-height:92vh;'
      + 'background:#fff;border-radius:2px;box-shadow:0 8px 40px rgba(43,49,123,.35);overflow:hidden;}'
      + '#chBookClose{position:absolute;top:10px;right:12px;z-index:2;border:0;background:#fff;'
      + 'color:#2B317B;font-family:inherit;font-size:.8rem;letter-spacing:.08em;'
      + 'text-transform:uppercase;padding:8px 12px;cursor:pointer;}'
      + '#chBookFrame{width:100%;height:520px;border:0;display:block;}';
    document.head.appendChild(css);

    box = document.createElement('div');
    box.id = 'chBookBox';
    box.hidden = true;
    box.innerHTML =
      '<div id="chBookCard">'
      + '<button type="button" id="chBookClose" aria-label="Close">Close</button>'
      + '<iframe id="chBookFrame" title="Book a briefing call" src="about:blank"></iframe>'
      + '</div>';
    document.body.appendChild(box);
    frame = box.querySelector('#chBookFrame');

    box.querySelector('#chBookClose').addEventListener('click', close);
    /* The dark surround closes it. The card itself does not. */
    box.addEventListener('click', function (e) { if (e.target === box) close(); });
  }

  /* THE BOX IS THE SIZE OF WHAT IS IN IT.
     The booking page is ours and on the same address, so its height can simply
     be read and the box set to it. Picking a day adds the times beside the
     calendar and makes it taller, so it is watched rather than measured once.
     It never grows past the screen, and only then does it scroll. */
  function fit() {
    if (!frame) return;
    var d;
    try { d = frame.contentDocument; } catch (e) { return; }
    if (!d || !d.body) return;
    var h = Math.max(d.body.scrollHeight, d.documentElement.scrollHeight);
    var cap = Math.round(window.innerHeight * 0.92) - 8;
    frame.style.height = Math.min(h, cap) + 'px';
  }

  function open() {
    build();
    /* Loaded only when asked for, so no page carries it on every visit. */
    frame.src = URL_BOOK;
    box.hidden = false;
    document.body.style.overflow = 'hidden';
    frame.addEventListener('load', function () {
      fit();
      try {
        var d = frame.contentDocument;
        if (window.ResizeObserver && d && d.body) {
          new ResizeObserver(fit).observe(d.body);
        }
      } catch (e) { }
    }, { once: true });
  }
  function close() {
    if (!box) return;
    box.hidden = true;
    frame.src = 'about:blank';   /* emptied, so it starts fresh next time */
    document.body.style.overflow = '';
  }

  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
  window.addEventListener('resize', function () { if (box && !box.hidden) fit(); });

  /* Every Schedule a Briefing Call points at the booking page itself, so that is
     what is caught here, however the address is written. A link to the contact
     page is left alone and simply opens the contact page.

     Catching the real address rather than a hash means the link is honest: open
     it in a new tab, or follow it out of an email, and it still lands on the
     booking page. The popup is a nicety on top, not the only way in. */
  document.addEventListener('click', function (e) {
    var a = e.target.closest ? e.target.closest('a[href]') : null;
    if (!a) return;
    if (!/(^|\/)book\/briefing-call\/?$/.test((a.getAttribute('href') || '').split('?')[0])) return;
    /* A new tab or a right click means they want the page itself. */
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
    if ((a.getAttribute('target') || '') === '_blank') return;
    e.preventDefault();
    open();
  });

  /* The contact page sends the brief first, then calls this. */
  window.chOpenBooking = open;
  window.chCloseBooking = close;
})();
