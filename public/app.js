// CV Base — pagina web. Nessuna libreria esterna; tutto il testo passa da textContent (niente XSS).
(() => {
  const TYPE_LABELS = {
    experience: 'Esperienze',
    project: 'Progetti',
    hackathon: 'Hackathon',
    achievement: 'Riconoscimenti',
    education: 'Formazione',
    skill: 'Competenze',
    language: 'Lingue',
  };
  const root = document.getElementById('app');
  const state = { entries: [], types: Object.keys(TYPE_LABELS), filter: 'all', q: '', lang: 'it-IT' };

  const getPw = () => { try { return sessionStorage.getItem('cvbase_pw') || ''; } catch { return ''; } };
  const setPw = (v) => { try { v ? sessionStorage.setItem('cvbase_pw', v) : sessionStorage.removeItem('cvbase_pw'); } catch { /* ignora */ } };

  function h(tag, attrs = {}, ...kids) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'class') el.className = v;
      else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
      else if (v !== false && v != null) el.setAttribute(k, v === true ? '' : v);
    }
    for (const kid of kids.flat()) if (kid != null && kid !== false) el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
    return el;
  }

  async function api(path, opts = {}) {
    const res = await fetch('/api' + path, {
      ...opts,
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + getPw(), ...(opts.headers || {}) },
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    if (res.status === 401) { setPw(''); renderLogin('Password non valida.'); throw new Error('auth'); }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.details ? data.details.join('; ') : data.error || 'Errore');
    return data;
  }

  // ---------- Dettatura vocale (Web Speech API del browser) ----------
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  let rec = null, recBtn = null;
  function stopDictation() { if (rec) { rec.onend = null; try { rec.stop(); } catch { /* ignora */ } } if (recBtn) recBtn.classList.remove('live'); rec = null; recBtn = null; }
  function toggleDictation(target, btn) {
    if (rec && recBtn === btn) return stopDictation();
    stopDictation();
    if (!SR) { alert('Il tuo browser non supporta la dettatura qui. Usa il microfono della tastiera del telefono: funziona in ogni campo di testo.'); return; }
    rec = new SR();
    rec.lang = state.lang;
    rec.continuous = true;
    rec.interimResults = false;
    rec.onresult = (ev) => {
      for (let i = ev.resultIndex; i < ev.results.length; i++) {
        if (ev.results[i].isFinal) target.value = (target.value ? target.value.trimEnd() + ' ' : '') + ev.results[i][0].transcript.trim();
      }
    };
    rec.onerror = () => stopDictation();
    rec.onend = () => stopDictation();
    recBtn = btn; btn.classList.add('live');
    try { rec.start(); } catch { stopDictation(); }
  }
  const langSelect = () => h('select', { 'aria-label': 'Lingua di dettatura', onchange: (e) => { state.lang = e.target.value; } },
    [['it-IT', 'Dettatura: italiano'], ['fr-FR', 'Dettatura: français'], ['en-US', 'Dettatura: English']].map(([v, t]) => h('option', { value: v, selected: v === state.lang }, t)));

  // ---------- Schermate ----------
  function renderLogin(msg = '') {
    stopDictation();
    const pw = h('input', { type: 'password', autocomplete: 'current-password', placeholder: 'Password', 'aria-label': 'Password' });
    const out = h('div', { class: 'msg' }, msg);
    const go = async () => {
      setPw(pw.value);
      try { await api('/check'); await load(); } catch (e) { if (e.message !== 'auth') out.textContent = 'Errore: ' + e.message; }
    };
    pw.addEventListener('keydown', (e) => { if (e.key === 'Enter') go(); });
    root.replaceChildren(h('div', { class: 'login' }, h('h1', {}, 'CV Base'), h('p', { class: 'hint' }, 'Il tuo archivio di esperienze per i CV.'), pw, out, h('button', { class: 'primary', onclick: go }, 'Entra')));
    pw.focus();
  }

  async function load() {
    const data = await api('/entries');
    state.entries = data.entries;
    renderList();
  }

  function renderList() {
    stopDictation();
    const q = state.q.trim().toLowerCase();
    const shown = state.entries.filter((e) => (state.filter === 'all' || e.type === state.filter) &&
      (!q || [e.title, e.org, e.description, e.result, e.tags.join(' ')].join(' ').toLowerCase().includes(q)));
    const chips = h('div', { class: 'chips' },
      ['all', ...state.types].map((t) => h('button', { class: t === state.filter ? 'on' : '', onclick: () => { state.filter = t; renderList(); } }, t === 'all' ? `Tutto (${state.entries.length})` : TYPE_LABELS[t])));
    const search = h('input', { type: 'search', placeholder: 'Cerca…', value: state.q, 'aria-label': 'Cerca', oninput: (e) => { state.q = e.target.value; renderList(); } });
    root.replaceChildren(
      h('header', { class: 'top' }, h('h1', {}, 'CV Base'),
        h('div', { class: 'row' }, h('button', { onclick: renderProfile }, 'Profilo'), h('button', { onclick: renderBackup }, 'Backup'), h('button', { class: 'ghost', onclick: () => { setPw(''); renderLogin(); } }, 'Esci'))),
      h('main', {}, search, chips,
        shown.length ? shown.map(card) : h('p', { class: 'hint' }, 'Nessuna voce.')),
      h('button', { class: 'primary fab', onclick: () => renderForm() }, '+ Aggiungi'));
    const s = root.querySelector('input[type=search]');
    if (state.q) { s.focus(); s.setSelectionRange(s.value.length, s.value.length); }
  }

  function card(e) {
    return h('div', { class: 'card' },
      h('h3', {}, e.title),
      h('div', { class: 'meta' }, [TYPE_LABELS[e.type], e.org, e.period].filter(Boolean).join(' · ')),
      e.description && h('p', {}, e.description),
      e.result && h('div', { class: 'result' }, h('b', {}, 'Risultato: '), e.result),
      e.tags.length ? h('div', { class: 'tags' }, e.tags.map((t) => h('span', { class: 'tag' }, t))) : null,
      e.link && /^https?:\/\//i.test(e.link) ? h('p', {}, h('a', { href: e.link, target: '_blank', rel: 'noopener noreferrer' }, e.link)) : null,
      e.note && h('div', { class: 'note' }, e.note),
      h('div', { class: 'row', 'data-actions': '' }, h('button', { onclick: () => renderForm(e) }, 'Modifica')));
  }

  function renderForm(entry) {
    stopDictation();
    const e = entry || { type: state.filter !== 'all' ? state.filter : 'experience', title: '', org: '', period: '', description: '', result: '', tags: [], link: '', note: '' };
    const inputs = {};
    const text = (key, label, multi = false, mic = false) => {
      const el = inputs[key] = h(multi ? 'textarea' : 'input', { value: multi ? null : e[key] ?? '' });
      if (multi) el.value = e[key] ?? '';
      return [h('label', {}, label), h('div', { class: 'field' }, el, mic ? h('button', { type: 'button', class: 'mic', 'aria-label': 'Detta', onclick: (ev) => toggleDictation(el, ev.currentTarget) }, '🎤') : null)];
    };
    const typeSel = inputs.type = h('select', {}, state.types.map((t) => h('option', { value: t, selected: t === e.type }, TYPE_LABELS[t])));
    const out = h('div', { class: 'msg' });
    const save = async () => {
      const body = {
        type: typeSel.value, title: inputs.title.value, org: inputs.org.value, period: inputs.period.value,
        description: inputs.description.value, result: inputs.result.value, link: inputs.link.value, note: inputs.note.value,
        tags: inputs.tags.value.split(',').map((t) => t.trim()).filter(Boolean),
      };
      try {
        if (entry) await api('/entries/' + entry.id, { method: 'PUT', body }); else await api('/entries', { method: 'POST', body });
        await load();
      } catch (err) { if (err.message !== 'auth') out.textContent = err.message; }
    };
    const del = entry && h('button', { class: 'danger', onclick: async () => { if (confirm('Eliminare questa voce?')) { try { await api('/entries/' + entry.id, { method: 'DELETE' }); await load(); } catch (err) { if (err.message !== 'auth') out.textContent = err.message; } } } }, 'Elimina');
    root.replaceChildren(
      h('header', { class: 'top' }, h('h1', {}, entry ? 'Modifica voce' : 'Nuova voce'), h('button', { class: 'ghost', onclick: () => renderList() }, 'Annulla')),
      h('main', {},
        h('div', { class: 'card' },
          h('label', {}, 'Tipo'), typeSel,
          text('title', 'Titolo'), text('org', 'Organizzazione / luogo'), text('period', 'Periodo (es. 2023 – 2025)'),
          h('label', {}, 'Lingua della dettatura'), langSelect(),
          text('description', 'Cosa hai fatto (azione e perimetro)', true, true),
          text('result', 'Risultato (numeri veri e verificabili)', true, true),
          text('tags', 'Tag, separati da virgola'), text('link', 'Link (https://…)'),
          text('note', 'Nota per te (es. "da completare")', true, true),
          out, h('div', { class: 'row' }, h('button', { class: 'primary', onclick: save }, 'Salva'), del))));
    inputs.tags.value = (e.tags || []).join(', ');
  }

  async function renderProfile() {
    stopDictation();
    const p = await api('/profile');
    const f = {};
    const field = (k, label, multi) => [h('label', {}, label), (f[k] = h(multi ? 'textarea' : 'input', {}))];
    const out = h('div', { class: 'msg' });
    const nodes = [field('name', 'Nome'), field('headline', 'Titolo / ruolo'), field('location', 'Città'), field('email', 'Email'), field('phone', 'Telefono'), field('links', 'Link (uno per riga)', true), field('notes', 'Note (età, patente, lingue…)', true)];
    root.replaceChildren(
      h('header', { class: 'top' }, h('h1', {}, 'Profilo'), h('button', { class: 'ghost', onclick: () => renderList() }, 'Indietro')),
      h('main', {}, h('div', { class: 'card' }, nodes, out, h('button', { class: 'primary', onclick: async () => {
        try {
          await api('/profile', { method: 'PUT', body: { name: f.name.value, headline: f.headline.value, location: f.location.value, email: f.email.value, phone: f.phone.value, notes: f.notes.value, links: f.links.value.split('\n').map((s) => s.trim()).filter(Boolean) } });
          out.textContent = 'Salvato.';
        } catch (err) { if (err.message !== 'auth') out.textContent = err.message; }
      } }, 'Salva'))));
    for (const k of ['name', 'headline', 'location', 'email', 'phone', 'notes']) f[k].value = p[k] || '';
    f.links.value = (p.links || []).join('\n');
  }

  function renderBackup() {
    stopDictation();
    const out = h('div', { class: 'msg' });
    const file = h('input', { type: 'file', accept: 'application/json' });
    root.replaceChildren(
      h('header', { class: 'top' }, h('h1', {}, 'Backup'), h('button', { class: 'ghost', onclick: () => renderList() }, 'Indietro')),
      h('main', {}, h('div', { class: 'card' },
        h('p', { class: 'hint' }, 'Scarica ogni tanto una copia dei tuoi dati. Se importi un file, sostituisce tutto quello che c\'è ora.'),
        h('button', { class: 'primary', onclick: async () => {
          const data = await api('/export');
          const a = h('a', { href: URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })), download: 'cv-base-backup.json' });
          document.body.append(a); a.click(); a.remove();
        } }, 'Scarica backup'),
        h('label', {}, 'Importa un backup'), file,
        h('button', { class: 'danger', onclick: async () => {
          if (!file.files[0]) { out.textContent = 'Scegli prima un file.'; return; }
          if (!confirm('Sostituire tutti i dati con quelli del file?')) return;
          try { await api('/import', { method: 'POST', body: JSON.parse(await file.files[0].text()) }); await load(); } catch (err) { if (err.message !== 'auth') out.textContent = 'Importazione non riuscita: ' + err.message; }
        } }, 'Importa'),
        out)));
  }

  if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
  if (getPw()) load().catch(() => renderLogin()); else renderLogin();
})();
