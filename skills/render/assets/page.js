const RAW = document.documentElement.outerHTML;

(() => {
  'use strict';

  let config = null;
  let state = null;
  let wired = false;

  function esc(s) {
    return String(s).replace(/[&<>"']/g, (ch) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    }[ch]));
  }

  function slug(s) {
    return String(s).toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  }

  function cap(s) {
    return s.charAt(0).toUpperCase() + s.slice(1);
  }

  function prefersReducedMotion() {
    return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
  }

  function isTyping(el) {
    if (!el) return false;
    return el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable === true;
  }

  function blockFor(anchor) {
    const safe = window.CSS?.escape ? CSS.escape(anchor) : anchor;
    return document.querySelector(`.anchored[data-anchor="${safe}"]`);
  }

  // -- state -------------------------------------------------------------

  function draftKey() {
    return 'render:' + config.file;
  }

  function safeParse(text) {
    try { return JSON.parse(text ?? 'null'); } catch { return null; }
  }

  function normalize(raw) {
    const s = raw || {};
    return { v: s.v || 1, updated: s.updated, page: s.page || {}, verdicts: s.verdicts || {}, comments: s.comments || [] };
  }

  function loadState() {
    const embedded = normalize(safeParse(document.getElementById('state')?.textContent));
    let draft = null;
    try { draft = safeParse(localStorage.getItem(draftKey())); } catch { /* draft unavailable */ }
    if (draft && draft.updated > (embedded.updated || '')) return normalize(draft);
    return embedded;
  }

  function persist() {
    state.updated = new Date().toISOString();
    try { localStorage.setItem(draftKey(), JSON.stringify(state)); } catch { /* storage unavailable */ }
    markDirty();
  }

  function clearDraft() {
    try { localStorage.removeItem(draftKey()); } catch { /* storage unavailable */ }
  }

  function markDirty() {
    const btn = document.querySelector('[data-action="save"]');
    if (!btn) return;
    btn.classList.add('is-dirty');
    btn.setAttribute('data-dirty', 'true');
    btn.textContent = 'Save changes';
  }

  // -- verdicts ------------------------------------------------------------

  // Order-independent: callable before Render.init() sets config, so it can
  // never read config.verdicts off a null config. Pre-init it returns an
  // empty data-for placeholder; init() (or a post-init call, which already
  // has the vocabulary) fills the buttons in.
  function verdictButtonsHtml(anchor) {
    const current = state?.verdicts[anchor]?.d;
    return config.verdicts
      .map((v) => `<button type="button" data-v="${esc(v)}" aria-pressed="${String(v === current)}">${esc(cap(v))}</button>`)
      .join('');
  }

  function verdictMarkup(anchor) {
    const inner = config?.verdicts ? verdictButtonsHtml(anchor) : '';
    return `<div class="verdict seg" role="group" aria-label="Verdict" data-for="${esc(anchor)}">${inner}</div>`;
  }

  function fillVerdicts() {
    if (!config.verdicts) return;
    for (const seg of document.querySelectorAll('.verdict.seg[data-for]')) {
      if (seg.children.length) continue;
      seg.innerHTML = verdictButtonsHtml(seg.dataset.for);
    }
  }

  function paintVerdict(block) {
    const anchor = block.dataset.anchor;
    const d = state.verdicts[anchor]?.d;
    const seg = block.querySelector('.verdict.seg');
    if (seg) {
      for (const btn of seg.querySelectorAll('button[data-v]')) {
        btn.setAttribute('aria-pressed', String(btn.dataset.v === d));
      }
    }
    if (d && config.verdicts) block.dataset.vrank = String(config.verdicts.indexOf(d) + 1);
    else delete block.dataset.vrank;
  }

  function setVerdict(block, value) {
    if (!block) return;
    const anchor = block.dataset.anchor;
    if (state.verdicts[anchor]?.d === value) delete state.verdicts[anchor];
    else state.verdicts[anchor] = { d: value };
    paintVerdict(block);
    persist();
    updateCounts();
  }

  function verdictTally() {
    const blocks = [...document.querySelectorAll('.anchored[data-anchor]')].filter((b) => b.querySelector('.verdict.seg'));
    const tally = Object.fromEntries(config.verdicts.map((v) => [v, 0]));
    tally.undecided = 0;
    tally.all = blocks.length;
    for (const b of blocks) {
      const d = state.verdicts[b.dataset.anchor]?.d;
      if (d && d in tally) tally[d] += 1;
      else tally.undecided += 1;
    }
    return tally;
  }

  // One pass to compute the tally, one pass over [data-count] to write it,
  // instead of a document query per key.
  function updateCounts() {
    const cells = document.querySelectorAll('[data-count]');
    if (!cells.length) return;
    const tally = config.verdicts ? verdictTally() : { comments: state.comments.length };
    for (const el of cells) {
      const key = el.dataset.count;
      if (key in tally) el.textContent = String(tally[key]);
    }
    const noun = document.querySelector('[data-noun]');
    if (noun) noun.textContent = noun.dataset.noun + (tally.comments === 1 ? '' : 's');
  }

  // Builds .counts and .seg[data-filter="verdict"] from the configured
  // vocabulary, replacing whatever the template shipped (templates ship both
  // as empty containers). Comments-only modes (verdicts: null) get a single
  // comment counter and no verdict filter.
  function buildToolbar() {
    const counts = document.querySelector('.counts');
    const filterSeg = document.querySelector('.seg[data-filter="verdict"]');
    if (config.verdicts) {
      if (counts) {
        counts.innerHTML = config.verdicts
          .map((v) => `<span><span data-count="${esc(v)}">0</span>${esc(v)}</span>`)
          .join('') + '<span><span data-count="undecided">0</span>undecided</span>';
      }
      if (filterSeg) {
        const items = [['all', 'All'], ['undecided', 'Undecided'], ...config.verdicts.map((v) => [v, cap(v)])];
        filterSeg.innerHTML = items
          .map(([value, label], i) => `<button type="button" data-value="${esc(value)}" aria-pressed="${i === 0}">${esc(label)}</button>`)
          .join('');
      }
    } else {
      if (counts) counts.innerHTML = '<span><span data-count="comments">0</span><span data-noun="comment">comments</span></span>';
      filterSeg?.remove();
    }
  }

  // -- comments --------------------------------------------------------------

  function commentsFor(anchor) {
    return state.comments.filter((c) => c.anchor === anchor);
  }

  function labelFor(block) {
    if (block.dataset.label) return block.dataset.label;
    const body = block.querySelector('.body') || block;
    const clone = body.cloneNode(true);
    clone.querySelectorAll('.mark, .comments, .composer').forEach((n) => n.remove());
    return clone.textContent.trim().slice(0, 80);
  }

  function formatTime(iso) {
    return String(iso).slice(0, 16).replace('T', ' ');
  }

  function renderComments(block) {
    const body = block.querySelector('.body');
    if (!body) return;
    body.querySelector(':scope > .comments')?.remove();
    const items = commentsFor(block.dataset.anchor);
    if (!items.length) return;
    const list = document.createElement('div');
    list.className = 'comments';
    list.innerHTML = items.map((c) => (
      `<div class="comment"><div class="comment-meta"><time datetime="${esc(c.at)}">${esc(formatTime(c.at))}</time>`
      + `<button type="button" class="btn-link" data-action="delete-comment" data-at="${esc(c.at)}">Delete</button></div>`
      + `<p class="comment-text">${esc(c.text)}</p></div>`
    )).join('');
    body.insertBefore(list, body.querySelector(':scope > .composer'));
  }

  function paintMark(block) {
    const mark = block.querySelector('.mark');
    if (!mark) return;
    const count = commentsFor(block.dataset.anchor).length;
    mark.textContent = count ? String(count) : '+';
    mark.classList.toggle('has', count > 0);
  }

  function openComposer(block) {
    if (!block) return;
    const body = block.querySelector('.body');
    if (!body) return;
    const existing = body.querySelector(':scope > .composer');
    if (existing) { existing.querySelector('textarea')?.focus(); return; }
    const composer = document.createElement('div');
    composer.className = 'composer';
    composer.innerHTML = (
      `<textarea aria-label="Comment" placeholder="Comment on ${esc(labelFor(block))}"></textarea>`
      + '<div class="composer-actions"><span class="meta"><kbd>Esc</kbd> to cancel</span>'
      + '<button type="button" class="btn" data-action="cancel-comment">Cancel</button>'
      + '<button type="button" class="btn btn-primary" data-action="submit-comment">Comment</button></div>'
    );
    body.appendChild(composer);
    composer.querySelector('textarea').focus();
  }

  function closeComposer(block) {
    block?.querySelector(':scope > .body > .composer')?.remove();
  }

  function submitComment(block) {
    if (!block) return;
    const textarea = block.querySelector(':scope > .body > .composer textarea');
    const text = textarea?.value.trim();
    if (!text) return;
    state.comments.push({
      anchor: block.dataset.anchor,
      label: labelFor(block),
      section: block.closest('[data-section]')?.dataset.section || '',
      text,
      at: new Date().toISOString(),
    });
    persist();
    closeComposer(block);
    renderComments(block);
    paintMark(block);
    updateCounts();
  }

  function deleteComment(block, at) {
    const anchor = block.dataset.anchor;
    const idx = state.comments.findIndex((c) => c.anchor === anchor && c.at === at);
    if (idx === -1) return;
    state.comments.splice(idx, 1);
    persist();
    renderComments(block);
    paintMark(block);
    updateCounts();
  }

  // -- page-level state ---------------------------------------------------------

  function getPage(key) {
    return state.page[key];
  }

  function setPage(key, value) {
    if (value === undefined || value === null) delete state.page[key];
    else state.page[key] = value;
    persist();
    paintPicks();
  }

  function paintPicks() {
    for (const btn of document.querySelectorAll('button[data-page-key][data-page-value]')) {
      const pressed = state.page[btn.dataset.pageKey] === btn.dataset.pageValue;
      btn.setAttribute('aria-pressed', String(pressed));
    }
  }

  function togglePick(btn) {
    const { pageKey, pageValue } = btn.dataset;
    setPage(pageKey, getPage(pageKey) === pageValue ? null : pageValue);
  }

  // -- filters ---------------------------------------------------------------

  function currentFilters() {
    const filters = {};
    for (const seg of document.querySelectorAll('.seg[data-filter]')) {
      const active = seg.querySelector('button[aria-pressed="true"]');
      filters[seg.dataset.filter] = active ? active.dataset.value : 'all';
    }
    return filters;
  }

  function blockHidden(block, filters) {
    const anchor = block.dataset.anchor;
    for (const [name, value] of Object.entries(filters)) {
      if (value === 'all') continue;
      if (name === 'verdict') {
        const d = state.verdicts[anchor]?.d;
        if (value === 'undecided' ? Boolean(d) : d !== value) return true;
      } else {
        const attr = block.getAttribute('data-facet-' + name);
        if (attr !== null && attr !== value) return true;
      }
    }
    return false;
  }

  // One pass over the blocks tallies each section's total/visible counts
  // alongside hiding them, instead of a second per-section querySelectorAll.
  function applyFilters() {
    const filters = currentFilters();
    const sectionCounts = new Map();
    for (const block of document.querySelectorAll('.anchored[data-anchor]')) {
      const hidden = blockHidden(block, filters);
      block.hidden = hidden;
      const section = block.closest('[data-section]');
      if (!section) continue;
      const counts = sectionCounts.get(section) || { total: 0, visible: 0 };
      counts.total += 1;
      if (!hidden) counts.visible += 1;
      sectionCounts.set(section, counts);
    }
    for (const section of document.querySelectorAll('[data-section]')) {
      updateSectionEmpty(section, filters, sectionCounts.get(section));
    }
  }

  function updateSectionEmpty(section, filters, counts) {
    const existing = section.querySelector('.empty[data-auto="filter"]');
    if (!counts || !counts.total || counts.visible) { existing?.remove(); return; }
    if (existing) return;
    const active = Object.entries(filters).filter(([, v]) => v !== 'all').map(([n, v]) => `${n}: ${v}`).join(', ') || 'the current filters';
    const empty = document.createElement('div');
    empty.className = 'empty';
    empty.dataset.auto = 'filter';
    empty.innerHTML = (
      `<p class="title">Nothing matches ${esc(active)}</p>`
      + '<p class="text">Every item in this section is hidden by the active filters.</p>'
      + '<button type="button" class="btn" data-action="clear-filters">Clear filters</button>'
    );
    section.appendChild(empty);
  }

  function clearFilters() {
    for (const seg of document.querySelectorAll('.seg[data-filter]')) {
      for (const btn of seg.querySelectorAll('button')) btn.setAttribute('aria-pressed', String(btn.dataset.value === 'all'));
    }
    applyFilters();
  }

  // -- theme -------------------------------------------------------------------

  function loadTheme() {
    try { return localStorage.getItem('render:theme') || 'auto'; } catch { return 'auto'; }
  }

  function applyTheme(value) {
    if (value === 'light' || value === 'dark') document.documentElement.setAttribute('data-theme', value);
    else document.documentElement.removeAttribute('data-theme');
    for (const btn of document.querySelectorAll('.seg[data-theme-toggle] button')) {
      btn.setAttribute('aria-pressed', String(btn.dataset.value === value));
    }
    try { localStorage.setItem('render:theme', value); } catch { /* storage unavailable */ }
  }

  // -- tabs, TOC ---------------------------------------------------------------

  function switchTab(tab) {
    const list = tab.closest('[role="tablist"]');
    for (const t of list.querySelectorAll('[role="tab"]')) {
      const on = t === tab;
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
      const panel = document.getElementById(t.getAttribute('aria-controls'));
      if (panel) panel.hidden = !on;
    }
  }

  let tocObserver = null;

  function observeToc() {
    tocObserver?.disconnect();
    tocObserver = null;
    const links = [...document.querySelectorAll('.toc a[href^="#"]')];
    if (!links.length || !('IntersectionObserver' in window)) return;
    const pairs = links
      .map((a) => [document.getElementById(a.getAttribute('href').slice(1)), a])
      .filter(([el]) => el);
    if (!pairs.length) return;
    pairs.sort((a, b) => (
      a[0].compareDocumentPosition(b[0]) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1
    ));
    const sections = pairs.map(([el]) => el);
    const linkFor = new Map(pairs);

    function setCurrent(link) {
      for (const [, a] of pairs) {
        if (a === link) a.setAttribute('aria-current', 'true');
        else a.removeAttribute('aria-current');
      }
    }

    // Active = the last section whose top has reached the sticky header's
    // bottom edge, recomputed from live geometry rather than trusted from the
    // IntersectionObserver entries, which only say a section is on screen,
    // not which one leads.
    function recompute() {
      const bar = document.querySelector('.toolbar');
      const threshold = (bar ? bar.getBoundingClientRect().bottom : 0) + 16;
      const atBottom = Math.ceil(window.scrollY + window.innerHeight) >= document.documentElement.scrollHeight;
      let active = sections[0];
      if (atBottom) {
        active = sections[sections.length - 1];
      } else {
        for (const el of sections) {
          if (el.getBoundingClientRect().top <= threshold) active = el;
        }
      }
      setCurrent(linkFor.get(active));
    }

    tocObserver = new IntersectionObserver(recompute, { threshold: [0, 0.5, 1] });
    for (const el of sections) tocObserver.observe(el);
    recompute();
  }

  // -- shortcuts panel -----------------------------------------------------------

  function toggleShortcuts() {
    const panel = document.getElementById('shortcuts');
    if (!panel) return;
    const show = panel.hidden;
    panel.hidden = !show;
    document.querySelector('[data-action="shortcuts"]')?.setAttribute('aria-expanded', String(show));
  }

  // -- keyboard navigation ---------------------------------------------------------

  function visibleBlocks() {
    return [...document.querySelectorAll('.anchored[data-anchor]')].filter((b) => !b.hidden);
  }

  function currentBlock() {
    return document.querySelector('.anchored.is-current');
  }

  function moveCurrent(delta) {
    const blocks = visibleBlocks();
    if (!blocks.length) return;
    const current = currentBlock();
    const idx = Math.min(Math.max((current ? blocks.indexOf(current) : -1) + delta, 0), blocks.length - 1);
    current?.classList.remove('is-current');
    const next = blocks[idx];
    next.classList.add('is-current');
    next.scrollIntoView({ block: 'nearest', behavior: prefersReducedMotion() ? 'auto' : 'smooth' });
  }

  function setCurrentVerdictByIndex(i) {
    const block = currentBlock();
    if (!block || !config.verdicts?.[i] || !block.querySelector('.verdict.seg')) return;
    setVerdict(block, config.verdicts[i]);
  }

  // -- digest -------------------------------------------------------------------

  function digestLabel(anchor) {
    return blockFor(anchor)?.dataset.label || anchor;
  }

  function buildDigest() {
    const lines = [];
    const pageEntries = Object.entries(state.page);
    if (pageEntries.length) {
      lines.push(`Decisions (${pageEntries.length})`);
      for (const [k, v] of pageEntries) lines.push(`  - ${k}: ${v}`);
    }
    if (config.verdicts) {
      for (const i of [1, 2, 0]) {
        const v = config.verdicts[i];
        if (v === undefined) continue;
        const entries = Object.entries(state.verdicts).filter(([, d]) => d.d === v);
        if (!entries.length) continue;
        lines.push(`${cap(v)} (${entries.length})`);
        for (const [anchor] of entries) lines.push(`  - ${digestLabel(anchor)}`);
      }
    }
    if (state.comments.length) {
      const resolved = state.comments.filter((c) => blockFor(c.anchor));
      const orphaned = state.comments.filter((c) => !blockFor(c.anchor));
      if (resolved.length) {
        lines.push(`Comments (${resolved.length})`);
        for (const c of resolved) lines.push(`  - [${c.section}] ${c.label}: ${c.text}`);
      }
      if (orphaned.length) {
        lines.push(`Orphaned comments (${orphaned.length})`);
        for (const c of orphaned) lines.push(`  - [${c.section}] ${c.label}: ${c.text}`);
      }
    }
    return lines.join('\n') || 'Nothing marked yet.';
  }

  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      try {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        ta.remove();
        return true;
      } catch {
        return false;
      }
    }
  }

  async function copyDigest(btn) {
    const original = btn.textContent;
    const ok = await copyText(buildDigest());
    btn.textContent = ok ? 'Copied' : original;
    setTimeout(() => { btn.textContent = original; }, 1500);
  }

  // -- save --------------------------------------------------------------------

  function buildDocument() {
    const openTag = '<script id="state" type="application/json">';
    const closeTag = '<' + '/script>';
    const start = RAW.indexOf(openTag) + openTag.length;
    const end = RAW.indexOf(closeTag, start);
    const json = JSON.stringify(state).replace(/</g, '\\u003c');
    return '<!doctype html>\n' + RAW.slice(0, start) + json + RAW.slice(end);
  }

  async function publish(doc) {
    if (typeof window.claude?.use === 'function') {
      try {
        const artifact = await window.claude.use('artifact');
        if (artifact) { await artifact.publish(doc); return; }
      } catch {
        // ponytail: artifact.publish can reject (conflict, not_granted); no retry UI, fall through to download
      }
    }
    download(doc);
  }

  function download(doc) {
    const blob = new Blob([doc], { type: 'text/html' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = config.file;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  async function save(btn) {
    const wasDirty = btn.classList.contains('is-dirty');
    btn.setAttribute('aria-busy', 'true');
    btn.disabled = true;
    btn.textContent = 'Saving';
    try {
      await publish(buildDocument());
      clearDraft();
      btn.classList.remove('is-dirty');
      btn.removeAttribute('data-dirty');
      btn.textContent = 'Save';
    } catch (e) {
      console.error(e);
      btn.textContent = wasDirty ? 'Save changes' : 'Save';
    } finally {
      btn.removeAttribute('aria-busy');
      btn.disabled = false;
    }
  }

  // -- event wiring --------------------------------------------------------------

  function onClick(ev) {
    const mark = ev.target.closest('.mark');
    if (mark) { openComposer(mark.closest('.anchored')); return; }

    const cancelBtn = ev.target.closest('[data-action="cancel-comment"]');
    if (cancelBtn) { closeComposer(cancelBtn.closest('.anchored')); return; }

    const submitBtn = ev.target.closest('[data-action="submit-comment"]');
    if (submitBtn) { submitComment(submitBtn.closest('.anchored')); return; }

    const deleteBtn = ev.target.closest('[data-action="delete-comment"]');
    if (deleteBtn) { deleteComment(deleteBtn.closest('.anchored'), deleteBtn.dataset.at); return; }

    const verdictBtn = ev.target.closest('.verdict.seg button[data-v]');
    if (verdictBtn) { setVerdict(verdictBtn.closest('.anchored'), verdictBtn.dataset.v); return; }

    const pickBtn = ev.target.closest('button[data-page-key][data-page-value]');
    if (pickBtn) { togglePick(pickBtn); return; }

    const filterBtn = ev.target.closest('.seg[data-filter] button');
    if (filterBtn) {
      const seg = filterBtn.closest('.seg');
      for (const btn of seg.querySelectorAll('button')) btn.setAttribute('aria-pressed', String(btn === filterBtn));
      applyFilters();
      return;
    }

    const clearBtn = ev.target.closest('[data-action="clear-filters"]');
    if (clearBtn) { clearFilters(); return; }

    const themeBtn = ev.target.closest('.seg[data-theme-toggle] button');
    if (themeBtn) { applyTheme(themeBtn.dataset.value); return; }

    const tab = ev.target.closest('[role="tab"]');
    if (tab) { switchTab(tab); return; }

    const shortcutsBtn = ev.target.closest('[data-action="shortcuts"]');
    if (shortcutsBtn) { toggleShortcuts(); return; }

    const digestBtn = ev.target.closest('[data-action="digest"]');
    if (digestBtn) { copyDigest(digestBtn); return; }

    const saveBtn = ev.target.closest('[data-action="save"]');
    if (saveBtn) save(saveBtn);
  }

  function onKeydown(ev) {
    const composer = ev.target.closest?.('.composer');
    if (composer) {
      if (ev.key === 'Escape') { closeComposer(composer.closest('.anchored')); ev.preventDefault(); }
      else if ((ev.ctrlKey || ev.metaKey) && ev.key === 'Enter') { submitComment(composer.closest('.anchored')); ev.preventDefault(); }
      return;
    }
    if (isTyping(ev.target)) return;
    switch (ev.key) {
      case 'j': moveCurrent(1); break;
      case 'k': moveCurrent(-1); break;
      case '1': case '2': case '3': setCurrentVerdictByIndex(Number(ev.key) - 1); break;
      case 'c': openComposer(currentBlock()); break;
      case '/': document.querySelector('.seg[data-filter] button')?.focus(); ev.preventDefault(); break;
      case '?': toggleShortcuts(); break;
      case 'Escape': {
        const openComposerEl = document.querySelector('.composer');
        if (openComposerEl) closeComposer(openComposerEl.closest('.anchored'));
        else if (!document.getElementById('shortcuts')?.hidden) toggleShortcuts();
        break;
      }
      default: break;
    }
  }

  function wireEvents() {
    if (wired) return;
    wired = true;
    document.addEventListener('click', onClick);
    document.addEventListener('keydown', onKeydown);
  }

  // -- render API ------------------------------------------------------------------

  function anchored({ anchor, label, cls = '', facets = {}, verdict: withVerdict = false, html = '' } = {}) {
    const facetAttrs = Object.entries(facets).map(([k, v]) => ` data-facet-${esc(k)}="${esc(v)}"`).join('');
    const classes = ('anchored ' + cls).trim();
    const body = withVerdict ? html + verdictMarkup(anchor) : html;
    return (
      `<article class="${esc(classes)}" data-anchor="${esc(anchor)}" data-label="${esc(label)}"${facetAttrs}>`
      + `<button class="mark" type="button" aria-label="Comment on ${esc(label)}">+</button>`
      + `<div class="body">${body}</div></article>`
    );
  }

  function hydrate() {
    for (const block of document.querySelectorAll('.anchored[data-anchor]')) {
      paintVerdict(block);
      renderComments(block);
      paintMark(block);
    }
    updateCounts();
    paintPicks();
  }

  // Escaped text with a <wbr> after every "/", so a long path wraps at a
  // segment boundary instead of mid-word.
  function pathMarkup(p) {
    return esc(p).split('/').join('/<wbr>');
  }

  // Safe to call more than once: it reloads state, rebuilds the toolbar and
  // verdict placeholders idempotently, and only wires document listeners
  // (wireEvents, observeToc) once each.
  function init(opts = {}) {
    config = { verdicts: opts.verdicts || null, file: opts.file || 'render.html', title: opts.title || document.title };
    state = loadState();
    buildToolbar();
    fillVerdicts();
    hydrate();
    applyTheme(loadTheme());
    applyFilters();
    observeToc();
    wireEvents();
  }

  window.Render = { esc, slug, cap, path: pathMarkup, anchored, verdict: verdictMarkup, init, getPage, setPage };
})();
