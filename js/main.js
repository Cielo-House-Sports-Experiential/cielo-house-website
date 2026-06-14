/* ============================================
 CIELO HOUSE Main JavaScript
 ============================================ */

'use strict';

/* --- Sticky Nav + Scroll behaviour --- */
const nav = document.querySelector('.nav');

function handleNavScroll() {
 if (!nav) return;
 if (window.scrollY > 60) {
 nav.classList.add('scrolled');
 } else {
 nav.classList.remove('scrolled');
 }
}

window.addEventListener('scroll', handleNavScroll, { passive: true });
handleNavScroll();

/* --- Mobile Menu --- */
const hamburger = document.querySelector('.nav__hamburger');
const mobileMenu = document.querySelector('.nav__mobile');
const mobileLinks = document.querySelectorAll('.nav__mobile-link');

if (hamburger && mobileMenu) {
 hamburger.addEventListener('click', () => {
 const isOpen = hamburger.classList.toggle('open');
 mobileMenu.classList.toggle('open', isOpen);
 document.body.style.overflow = isOpen ? 'hidden' : '';
 });

 mobileLinks.forEach(link => {
 link.addEventListener('click', () => {
 hamburger.classList.remove('open');
 mobileMenu.classList.remove('open');
 document.body.style.overflow = '';
 });
 });

 // Services dropdown inside the mobile menu
 const mobileToggle = document.querySelector('.nav__mobile-toggle');
 if (mobileToggle) {
 mobileToggle.addEventListener('click', () => {
 const group = mobileToggle.closest('.nav__mobile-group');
 if (group) group.classList.toggle('open');
 mobileToggle.setAttribute('aria-expanded', group && group.classList.contains('open') ? 'true' : 'false');
 });
 }
 // Sub-links navigate, so close the menu like the other links
 document.querySelectorAll('.nav__mobile-sublink').forEach(link => {
 link.addEventListener('click', () => {
 hamburger.classList.remove('open');
 mobileMenu.classList.remove('open');
 document.body.style.overflow = '';
 });
 });
}

/* --- Scroll Animations (Intersection Observer) --- */
const animateEls = document.querySelectorAll('[data-animate]');

if ('IntersectionObserver' in window && animateEls.length) {
 const observer = new IntersectionObserver(
 (entries) => {
 entries.forEach(entry => {
 if (entry.isIntersecting) {
 entry.target.classList.add('animated');
 observer.unobserve(entry.target);
 }
 });
 },
 { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
 );

 animateEls.forEach(el => observer.observe(el));
}

/* --- Active Nav Link --- */
const navLinks = document.querySelectorAll('.nav__link');
const currentPath = window.location.pathname.split('/').pop() || 'index.html';

navLinks.forEach(link => {
 const href = link.getAttribute('href');
 if (href === currentPath || (currentPath === '' && href === 'index.html')) {
 link.classList.add('active');
 }
});

/* --- Testimonial Slider --- */
const track = document.querySelector('.testimonial-track');
const prevBtn = document.querySelector('.testimonial-nav__btn--prev');
const nextBtn = document.querySelector('.testimonial-nav__btn--next');

if (track) {
 let currentIndex = 0;
 const cards = track.querySelectorAll('.testimonial-card');
 const total = cards.length;
 const visible = window.innerWidth < 768 ? 1 : 2;

 function updateSlider() {
 const cardWidth = cards[0].getBoundingClientRect().width;
 const gap = 24;
 const offset = currentIndex * (cardWidth + gap);
 track.style.transform = `translateX(-${offset}px)`;
 }

 if (nextBtn) {
 nextBtn.addEventListener('click', () => {
 currentIndex = Math.min(currentIndex + 1, total - visible);
 updateSlider();
 });
 }

 if (prevBtn) {
 prevBtn.addEventListener('click', () => {
 currentIndex = Math.max(currentIndex - 1, 0);
 updateSlider();
 });
 }
}

/* --- Counter Animation for Stats --- */
function animateCounter(el, target, duration = 2000) {
 const start = performance.now();
 const isDecimal = target % 1 !== 0;

 function update(time) {
 const elapsed = time - start;
 const progress = Math.min(elapsed / duration, 1);
 // Ease out quad
 const eased = 1 - Math.pow(1 - progress, 3);
 const current = eased * target;

 el.textContent = isDecimal
 ? current.toFixed(1)
 : Math.floor(current).toLocaleString() + (el.dataset.suffix || '');

 if (progress < 1) requestAnimationFrame(update);
 }

 requestAnimationFrame(update);
}

const statNumbers = document.querySelectorAll('.stat__number[data-count]');

if ('IntersectionObserver' in window && statNumbers.length) {
 const counterObserver = new IntersectionObserver(
 (entries) => {
 entries.forEach(entry => {
 if (entry.isIntersecting) {
 const el = entry.target;
 const target = parseFloat(el.dataset.count);
 animateCounter(el, target);
 counterObserver.unobserve(el);
 }
 });
 },
 { threshold: 0.5 }
 );

 statNumbers.forEach(el => counterObserver.observe(el));
}

/* Contact form handling lives on contact.html (real Web3Forms submit). The old
   placeholder handler here was dead code (faked success, no endpoint) and has
   been removed so it can't double-bind to the live enquiry form. */

/* --- Smooth scroll for anchor links --- */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
 anchor.addEventListener('click', function (e) {
 const target = document.querySelector(this.getAttribute('href'));
 if (target) {
 e.preventDefault();
 const offset = 80; // nav height
 const top = target.getBoundingClientRect().top + window.scrollY - offset;
 window.scrollTo({ top, behavior: 'smooth' });
 }
 });
});

/* --- Parallax on Hero background (image backgrounds only;
 the hero video is fixed full-bleed and must not be transformed) --- */
const heroBg = document.querySelector('.hero__bg img');

if (heroBg && window.innerWidth > 768) {
 window.addEventListener('scroll', () => {
 const scrolled = window.scrollY;
 const rate = scrolled * 0.3;
 heroBg.style.transform = `translateY(${rate}px)`;
 }, { passive: true });
}


/* ============================================
 CONTACT WIDGET Cielo AI Concierge
 ============================================ */
(function () {
 'use strict';

 // Resolve asset paths regardless of page depth
 function assetPath(rel) {
 var scripts = document.querySelectorAll('script[src*="main.js"]');
 if (scripts.length) {
 var src = scripts[scripts.length - 1].getAttribute('src');
 var base = src.replace(/js\/main\.js.*$/, '');
 return base + rel;
 }
 return '/' + rel;
 }

 var mascotSrc = assetPath('images/cielo-mascot/cielo-mascot-icon-2.png');
 var headerImgSrc = assetPath('images/cielo-mascot/chat-box-header/mascot-header.png');
 var chatHeaderImgSrc = assetPath('images/cielo-mascot/chat-box-header/mascot-header-inside-chat.png');
 var tagLight = assetPath('images/cielo-mascot/chat-tag/light-blue.png');
 var tagWhite = assetPath('images/cielo-mascot/chat-tag/white.png');

 // ── HTML ─────────────────────────────────────
 var HTML = '\
<div class="cw-overlay" id="cw-overlay" aria-hidden="true"></div>\
\
<div class="cw-panel" id="cw-panel" role="dialog" aria-modal="true" aria-labelledby="cw-panel-title" aria-hidden="true">\
\
 <!-- VIEW: Home -->\
 <div class="cw-view cw-view--home" id="cw-view-home">\
 <div class="cw-header">\
 <button class="cw-header__close" id="cw-close-home" aria-label="Close">\
 <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M1 1l12 12M13 1L1 13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>\
 </button>\
 <div class="cw-header__sub" id="cw-panel-title">Built for the Moment, Created to Last</div>\
 </div>\
 <div class="cw-body">\
 <p class="cw-body__copy">Have a question about our brand activations or premium hospitality experiences?</p>\
 <div class="cw-actions">\
 <button class="cw-btn cw-btn--primary" id="cw-open-chat" aria-label="Chat with our team">\
 <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>\
 Chat With Our Team\
 </button>\
 <a href="https://www.cielohouse.com.au/contact.html#discovery-call" class="cw-btn cw-btn--secondary" aria-label="Schedule a Briefing Call">\
 <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>\
 Schedule a Briefing Call\
 </a>\
 </div>\
 <p class="cw-footer">Cielo House Experiential &amp; Events</p>\
 </div>\
 </div>\
\
 <!-- VIEW: Chat -->\
 <div class="cw-view cw-view--chat" id="cw-view-chat" style="display:none;">\
 <div class="cw-chat-header">\
 <button class="cw-chat-back" id="cw-chat-back" aria-label="Back to menu">\
 <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="15 18 9 12 15 6"/></svg>\
 </button>\
 <div class="cw-chat-header__center">\
 <img class="cw-chat-header__img" src="' + chatHeaderImgSrc + '" alt="Talk with Cielo House Team" />\
 <div class="cw-chat-header__status" style="align-self:flex-start;padding-left:1.8rem;"><span class="cw-status-dot"></span> Online</div>\
 </div>\
 <button class="cw-header__close" id="cw-close-chat" aria-label="Close">\
 <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M1 1l12 12M13 1L1 13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>\
 </button>\
 </div>\
 <div class="cw-messages" id="cw-messages" role="log" aria-live="polite" aria-label="Chat messages"></div>\
 <div class="cw-input-area">\
 <textarea class="cw-input" id="cw-input" rows="1" placeholder="Ask about our services, events…" aria-label="Type your message" maxlength="500"></textarea>\
 <button class="cw-send" id="cw-send" aria-label="Send message" disabled>\
 <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>\
 </button>\
 </div>\
 </div>\
\
</div>\
\
<!-- Trigger: two images swap via CSS class -->\
<button class="cw-trigger" id="cw-trigger" aria-expanded="false" aria-controls="cw-panel" aria-label="Open Cielo House contact panel">\
 <img class="cw-tag cw-tag--on-light" src="' + tagLight + '" alt="Talk with Cielo" />\
 <img class="cw-tag cw-tag--on-dark" src="' + tagWhite + '" alt="Talk with Cielo" />\
</button>';

 // ── Inject ───────────────────────────────────
 var container = document.createElement('div');
 container.innerHTML = HTML;
 document.body.appendChild(container);

 // ── Visibility gated by the dashboard toggle (Supabase). Hidden until
 //    confirmed enabled, so OFF is the safe default. ──
 container.style.display = 'none';
 (function () {
 var SB = 'https://nkabuhbkuzcxajzrlenj.supabase.co';
 var SK = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5rYWJ1aGJrdXpjeGFqenJsZW5qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM0MzMwODQsImV4cCI6MjA4OTAwOTA4NH0.XsqejRlI7Cf_yu0Q6zOGAmBzWJKPeTZbIevjJ-3nWvo';
 fetch(SB + '/rest/v1/chat_widget_settings?id=eq.main&select=enabled', { headers: { apikey: SK, Authorization: 'Bearer ' + SK } })
 .then(function (r) { return r.ok ? r.json() : null; })
 .then(function (rows) { if (rows && rows[0] && rows[0].enabled === true) container.style.display = ''; })
 .catch(function () {});
 })();

 // ── Refs ─────────────────────────────────────
 var trigger = document.getElementById('cw-trigger');
 var panel = document.getElementById('cw-panel');
 var overlay = document.getElementById('cw-overlay');
 var closeHome = document.getElementById('cw-close-home');
 var closeChat = document.getElementById('cw-close-chat');
 var openChat = document.getElementById('cw-open-chat');
 var chatBack = document.getElementById('cw-chat-back');
 var viewHome = document.getElementById('cw-view-home');
 var viewChat = document.getElementById('cw-view-chat');
 var messages = document.getElementById('cw-messages');
 var input = document.getElementById('cw-input');
 var sendBtn = document.getElementById('cw-send');

 var chatHistory = [];
 var isTyping = false;
 var chatInitialised = false;

 // ── Panel open / close ────────────────────────
 function openPanel() {
 panel.classList.add('cw-open');
 overlay.classList.add('cw-open');
 panel.setAttribute('aria-hidden', 'false');
 trigger.setAttribute('aria-expanded', 'true');
 setTimeout(function () { closeHome.focus(); }, 80);
 }

 function closePanel() {
 panel.classList.remove('cw-open');
 overlay.classList.remove('cw-open');
 panel.setAttribute('aria-hidden', 'true');
 trigger.setAttribute('aria-expanded', 'false');
 trigger.focus();
 }

 trigger.addEventListener('click', function () {
 panel.classList.contains('cw-open') ? closePanel() : openPanel();
 });

 [closeHome, closeChat].forEach(function (btn) { btn.addEventListener('click', closePanel); });
 overlay.addEventListener('click', closePanel);
 document.addEventListener('mousedown', function (e) {
 if (panel.classList.contains('cw-open') && !panel.contains(e.target) && e.target !== trigger) closePanel();
 });
 document.addEventListener('keydown', function (e) {
 if (e.key === 'Escape' && panel.classList.contains('cw-open')) closePanel();
 });

 // ── View switching ────────────────────────────
 function showChat() {
 viewHome.style.display = 'none';
 viewChat.style.display = 'flex';
 if (!chatInitialised) initChat();
 input.focus();
 }

 function showHome() {
 viewChat.style.display = 'none';
 viewHome.style.display = 'flex';
 }

 openChat.addEventListener('click', showChat);
 chatBack.addEventListener('click', showHome);

 // ── Chat ─────────────────────────────────────
 function initChat() {
 chatInitialised = true;
 appendMessage('agent', "<strong>Welcome to Cielo House Experiential & Events.</strong> We are experts in brand activations and premium hospitality events and experiences. What services are you interested in?", true);
 appendQuickReplies([
 { label: 'Brand Activation', value: 'I am interested in Brand Activation.' },
 { label: 'Corporate Hospitality', value: 'I am interested in Corporate Hospitality.' }
 ]);
 }

 function appendQuickReplies(options) {
 var wrap = document.createElement('div');
 wrap.className = 'cw-quick-replies';
 options.forEach(function (opt) {
 var btn = document.createElement('button');
 btn.className = 'cw-quick-btn';
 btn.textContent = opt.label;
 btn.addEventListener('click', function () {
 wrap.remove();
 appendMessage('user', opt.label);
 chatHistory.push({ role: 'user', content: opt.value });
 isTyping = true;
 showTyping();
 var body = { messages: chatHistory };
 var knowledge = getKnowledge();
 if (knowledge) body.knowledge = knowledge;
 fetch('/api/chat', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify(body)
 }).then(function (res) {
 removeTyping();
 if (!res.ok) throw new Error('err');
 return res.json();
 }).then(function (data) {
 var reply = data.reply || 'Please email us at connect@cielohouse.com.au and we will be in touch within 24 hours.';
 appendMessage('agent', reply);
 chatHistory.push({ role: 'assistant', content: reply });
 isTyping = false;
 }).catch(function () {
 removeTyping();
 appendMessage('agent', 'Please email us at connect@cielohouse.com.au and we will be in touch within 24 hours.');
 isTyping = false;
 });
 });
 wrap.appendChild(btn);
 });
 messages.appendChild(wrap);
 messages.scrollTop = messages.scrollHeight;
 }

 function appendMessage(role, text, isHtml) {
 var wrap = document.createElement('div');
 wrap.className = 'cw-msg cw-msg--' + role;
 if (role === 'agent') {
 var av = document.createElement('div');
 av.className = 'cw-msg__avatar';
 var avImg = document.createElement('img');
 avImg.src = mascotSrc; avImg.alt = ''; avImg.setAttribute('aria-hidden','true');
 av.appendChild(avImg);
 wrap.appendChild(av);
 }
 var bubble = document.createElement('div');
 bubble.className = 'cw-msg__bubble';
 if (isHtml) { bubble.innerHTML = text; } else { bubble.textContent = text; }
 wrap.appendChild(bubble);
 messages.appendChild(wrap);
 messages.scrollTop = messages.scrollHeight;
 }

 function showTyping() {
 var wrap = document.createElement('div');
 wrap.className = 'cw-msg cw-msg--agent cw-msg--typing';
 wrap.id = 'cw-typing';
 var av = document.createElement('div');
 av.className = 'cw-msg__avatar';
 var avImg = document.createElement('img');
 avImg.src = mascotSrc; avImg.alt = '';
 av.appendChild(avImg); wrap.appendChild(av);
 var bubble = document.createElement('div');
 bubble.className = 'cw-msg__bubble cw-typing-dots';
 bubble.innerHTML = '<span></span><span></span><span></span>';
 wrap.appendChild(bubble);
 messages.appendChild(wrap);
 messages.scrollTop = messages.scrollHeight;
 }

 function removeTyping() {
 var t = document.getElementById('cw-typing');
 if (t) t.remove();
 }

 function getKnowledge() {
 try { return JSON.parse(localStorage.getItem('ch_ai_knowledge') || 'null'); } catch (e) { return null; }
 }

 function sendMessage() {
 var text = input.value.trim();
 if (!text || isTyping) return;
 input.value = ''; input.style.height = 'auto';
 sendBtn.disabled = true; isTyping = true;
 appendMessage('user', text);
 chatHistory.push({ role: 'user', content: text });
 showTyping();
 var body = { messages: chatHistory };
 var knowledge = getKnowledge();
 if (knowledge) body.knowledge = knowledge;
 fetch('/api/chat', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify(body)
 }).then(function (res) {
 removeTyping();
 if (!res.ok) throw new Error('err');
 return res.json();
 }).then(function (data) {
 var reply = data.reply || "I'm having trouble connecting right now. Please email us at connect@cielohouse.com.au.";
 appendMessage('agent', reply);
 chatHistory.push({ role: 'assistant', content: reply });
 isTyping = false;
 }).catch(function () {
 removeTyping();
 appendMessage('agent', "I'm having a moment of trouble connecting. Please email us at connect@cielohouse.com.au and we'll get back to you within 24 hours.");
 isTyping = false;
 });
 }

 sendBtn.addEventListener('click', sendMessage);
 input.addEventListener('keydown', function (e) {
 if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
 });
 input.addEventListener('input', function () {
 sendBtn.disabled = !input.value.trim();
 input.style.height = 'auto';
 input.style.height = Math.min(input.scrollHeight, 96) + 'px';
 });

 // ── Adaptive trigger image ────────────────────
 // Swaps between light-blue and dark-blue chat-tag based on section background
 var DARK_CLASSES = ['section--dark','cta-section','process','hero','footer'];
 // Matches: #2B317B, #1a1f52, #668DC6 (medium blue), pure black, near-black
 var DARK_BG_RE = /^rgb\((43,\s*49,\s*123|26,\s*31,\s*82|102,\s*141,\s*198|0,\s*0,\s*0|27,\s*27,\s*27)\)$/;

 function isDarkBg(el) {
 while (el && el !== document.body) {
 var cls = el.className || '';
 if (typeof cls === 'string' && DARK_CLASSES.some(function(c){ return cls.indexOf(c) > -1; })) return true;
 var bg = getComputedStyle(el).backgroundColor.replace(/\s/g,'');
 if (DARK_BG_RE.test(bg)) return true;
 el = el.parentElement;
 }
 return false;
 }

 function checkTriggerBackground() {
 var rect = trigger.getBoundingClientRect();
 trigger.style.pointerEvents = 'none';
 var el = document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2);
 trigger.style.pointerEvents = '';
 trigger.classList.toggle('cw-trigger--on-dark', el ? isDarkBg(el) : false);
 }

 window.addEventListener('scroll', checkTriggerBackground, { passive: true });
 window.addEventListener('resize', checkTriggerBackground, { passive: true });
 checkTriggerBackground();

})();


/* ============================================
 FAQ Render from localStorage, accordion, schema
 ============================================ */
(function () {
 var FAQ_KEY = 'ch_faqs';

 // Default FAQs SEO-optimised for Google featured snippets (~280-480 chars)
 var DEFAULT_FAQS = [
 {
 q: "What does a sports event activation agency do?",
 a: "A sports event activation agency designs and delivers brand experiences at major sporting events from fan engagement zones and sponsor inventory build-outs to branded hospitality lounges and on-site content capture. Cielo House manages the full production chain, from concept through to bump-out, at events including the F1 Australian Grand Prix, Supercars Championship, and WSL surfing competitions."
 },
 {
 q: "How can brand activations at sporting events grow my business?",
 a: "Brand activations at sporting events place your brand directly in front of a highly engaged, passionate audience at peak attention moments. Done well, they generate earned media, social content, and genuine brand recall that outlasts the event itself. Cielo House designs activations specifically around the venue, the crowd, and the commercial outcome your brand needs not generic creative applied to a sporting environment."
 },
 {
 q: "How do I organise corporate hospitality at a major Australian sporting event?",
 a: "Organising corporate hospitality at a major Australian sporting event starts with understanding your guest list, the event, and the standard you want to hold from arrival to departure. Cielo House plans the full sequence branded lounge concept and fit-out, talent integration, service standards, and crew management so the experience reflects your brand from the moment guests arrive to the final bump-out."
 },
 {
 q: "What sporting events does Cielo House work at?",
 a: "Cielo House delivers activations and hospitality programmes at major Australian sporting events including the Formula 1 Australian Grand Prix in Melbourne, the Boost Mobile Gold Coast 500 (Supercars Championship), WSL Rip Curl Pro Bells Beach, and Australian Boardriders Battle. The agency is based on the Gold Coast and has strong relationships with Gold Coast and Queensland sporting properties."
 },
 {
 q: "What is the process for briefing Cielo House on an activation or hospitality project?",
 a: "The process starts with a brief discussion not a sales call. Bring the event you are activating at, the activation type (brand zone, hospitality, or both), a rough budget bracket, and the outcome you need for your brand. From that conversation you will know whether Cielo House is the right fit and what delivery will take. Contact us at connect@cielohouse.com.au to start."
 }
 ];

 // Live FAQs from Supabase (same on every device, managed in the dashboard).
 var FAQ_SB = 'https://nkabuhbkuzcxajzrlenj.supabase.co';
 var FAQ_SK = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5rYWJ1aGJrdXpjeGFqenJsZW5qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM0MzMwODQsImV4cCI6MjA4OTAwOTA4NH0.XsqejRlI7Cf_yu0Q6zOGAmBzWJKPeTZbIevjJ-3nWvo';
 function loadFaqs() {
 fetch(FAQ_SB + '/rest/v1/faqs?select=question,answer&order=sort_order.asc', { headers: { apikey: FAQ_SK, Authorization: 'Bearer ' + FAQ_SK } })
 .then(function (r) { return r.ok ? r.json() : null; })
 .then(function (rows) {
 if (!rows || !rows.length) { renderFaqs(DEFAULT_FAQS); return; }
 renderFaqs(rows.map(function (f) { return { q: f.question, a: f.answer }; }));
 })
 .catch(function () { renderFaqs(DEFAULT_FAQS); });
 }

 function renderFaqs(faqs) {
 var list = document.getElementById('faq-list');
 if (!list) return;
 if (!faqs || !faqs.length) faqs = DEFAULT_FAQS;
 list.innerHTML = '';

 faqs.forEach(function (faq, idx) {
 var item = document.createElement('div');
 item.className = 'faq-item';
 item.setAttribute('role', 'listitem');

 var id = 'faq-answer-' + idx;
 item.innerHTML =
 '<button class="faq-question" aria-expanded="false" aria-controls="' + id + '">' +
 escHtml(faq.q) +
 '<span class="faq-chevron" aria-hidden="true">' +
 '<svg width="10" height="6" viewBox="0 0 10 6" fill="none"><path d="M1 1l4 4 4-4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>' +
 '</span>' +
 '</button>' +
 '<div class="faq-answer" id="' + id + '" role="region">' +
 '<div class="faq-answer-inner">' + escHtml(faq.a) + '</div>' +
 '</div>';

 var btn = item.querySelector('.faq-question');
 var answer = item.querySelector('.faq-answer');

 btn.addEventListener('click', function () {
 var isOpen = btn.getAttribute('aria-expanded') === 'true';
 // Close all others
 document.querySelectorAll('.faq-question[aria-expanded="true"]').forEach(function (b) {
 if (b !== btn) {
 b.setAttribute('aria-expanded', 'false');
 b.closest('.faq-item').querySelector('.faq-answer').style.maxHeight = '0';
 }
 });
 if (isOpen) {
 btn.setAttribute('aria-expanded', 'false');
 answer.style.maxHeight = '0';
 } else {
 btn.setAttribute('aria-expanded', 'true');
 answer.style.maxHeight = answer.scrollHeight + 'px';
 }
 });

 list.appendChild(item);
 });

 // Inject FAQ schema for Google rich results
 var schemaEl = document.getElementById('faq-schema');
 if (schemaEl) {
 schemaEl.textContent = JSON.stringify({
 "@context": "https://schema.org",
 "@type": "FAQPage",
 "mainEntity": faqs.map(function (f) {
 return {
 "@type": "Question",
 "name": f.q,
 "acceptedAnswer": { "@type": "Answer", "text": f.a }
 };
 })
 });
 }
 }

 function escHtml(str) {
 return String(str)
 .replace(/&/g, '&amp;')
 .replace(/</g, '&lt;')
 .replace(/>/g, '&gt;')
 .replace(/"/g, '&quot;');
 }

 loadFaqs();
})();

/* ============================================
   Newsletter subscribe — saves to Supabase (subscribers table), not localStorage.
   Used by the "Join Our Mailing List" forms across the site.
   ============================================ */
window.cieloSubscribe = function (form, source) {
  var input = form.querySelector('input[type=email]');
  var btn = form.querySelector('button[type="submit"]') || form.querySelector('button');
  var email = input && input.value ? input.value.trim() : '';
  if (!email) return false;
  var SB = 'https://nkabuhbkuzcxajzrlenj.supabase.co';
  var SK = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5rYWJ1aGJrdXpjeGFqenJsZW5qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM0MzMwODQsImV4cCI6MjA4OTAwOTA4NH0.XsqejRlI7Cf_yu0Q6zOGAmBzWJKPeTZbIevjJ-3nWvo';
  // Plain insert (no upsert): the subscriber list is no longer anon-readable, so
  // the on-conflict upsert path is blocked by RLS. A duplicate email just returns
  // a harmless 409 that we ignore — the UI still confirms.
  fetch(SB + '/rest/v1/subscribers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'apikey': SK, 'Authorization': 'Bearer ' + SK, 'Prefer': 'return=minimal' },
    body: JSON.stringify({ email: email, source: source || 'website' })
  }).catch(function () {});
  if (btn) btn.textContent = 'Subscribed ✓';
  if (input) input.value = '';
  return false;
};
