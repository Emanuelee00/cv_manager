// Collaudo completo in locale: API web + server MCP con il client ufficiale.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import http from 'node:http';
import { createApp } from './server.js';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';

const PW = 'password-di-prova-123';
const KEY = 'chiave-segreta-di-prova-0123456789abcdef';
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cvbase-'));

// 1) Il server NON deve partire senza segreti
assert.throws(() => createApp({ appPassword: '', mcpSecret: KEY, dataDir: dir }), /APP_PASSWORD/);
assert.throws(() => createApp({ appPassword: PW, mcpSecret: 'corta', dataDir: dir }), /MCP_SECRET/);
console.log('ok  rifiuta segreti mancanti o corti');

const { app, store } = createApp({ appPassword: PW, mcpSecret: KEY, dataDir: dir });
const server = http.createServer(app);
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${server.address().port}`;
const auth = { Authorization: 'Bearer ' + PW, 'Content-Type': 'application/json' };
const j = async (p, o = {}) => { const r = await fetch(base + p, o); return { status: r.status, body: await r.json().catch(() => null) }; };

// 2) API protetta
assert.equal((await j('/api/entries')).status, 401);
assert.equal((await j('/api/entries', { headers: { Authorization: 'Bearer sbagliata' } })).status, 401);
const list = await j('/api/entries', { headers: auth });
assert.equal(list.status, 200);
assert.ok(list.body.entries.length >= 20, 'dati iniziali caricati');
console.log(`ok  API protetta, ${list.body.entries.length} voci iniziali`);

// 3) CRUD + validazione
const bad = await j('/api/entries', { method: 'POST', headers: auth, body: JSON.stringify({ type: 'boh', title: '' }) });
assert.equal(bad.status, 400);
const badLink = await j('/api/entries', { method: 'POST', headers: auth, body: JSON.stringify({ type: 'project', title: 'x', link: 'javascript:alert(1)' }) });
assert.equal(badLink.status, 400, 'link non http rifiutato');
const created = await j('/api/entries', { method: 'POST', headers: auth, body: JSON.stringify({ type: 'project', title: 'Prova Kubernetes', tags: ['Kubernetes', 'Helm'], description: 'Cluster di prova' }) });
assert.equal(created.status, 201);
const id = created.body.id;
const upd = await j('/api/entries/' + id, { method: 'PUT', headers: auth, body: JSON.stringify({ result: 'Deploy in 3 minuti' }) });
assert.equal(upd.body.result, 'Deploy in 3 minuti');
assert.equal(upd.body.title, 'Prova Kubernetes', 'aggiornamento parziale non cancella gli altri campi');
console.log('ok  creare, modificare, validare');

// 4) Pagina statica + intestazioni
const page = await fetch(base + '/');
assert.equal(page.status, 200);
assert.match(page.headers.get('content-security-policy'), /script-src 'self'/);
assert.match(await page.text(), /CV Base/);
assert.equal((await fetch(base + '/app.js')).status, 200);
const man = await fetch(base + '/manifest.webmanifest');
assert.equal(man.status, 200);
assert.match(man.headers.get('content-type'), /json/);
const manifest = await man.json();
assert.equal(manifest.display, 'standalone');
for (const i of manifest.icons) assert.equal((await fetch(base + i.src)).status, 200);
assert.equal((await fetch(base + '/sw.js')).status, 200);
console.log('ok  pagina servita con CSP');

// 5) MCP: senza chiave giusta -> 404
const noKey = await fetch(base + '/mcp/chiave-sbagliata', { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json, text/event-stream' }, body: '{}' });
assert.equal(noKey.status, 404);
assert.equal((await fetch(base + '/mcp')).status, 404);
console.log('ok  MCP con chiave sbagliata o assente: 404');

// 6) MCP con il client ufficiale
const client = new Client({ name: 'test', version: '1.0.0' });
await client.connect(new StreamableHTTPClientTransport(new URL(`${base}/mcp/${KEY}`)));
const tools = (await client.listTools()).tools.map((t) => t.name).sort();
assert.deepEqual(tools, ['add_entry', 'get_entry', 'get_profile', 'list_entries', 'rank_for_offer', 'search_entries', 'update_entry']);
assert.ok(!tools.includes('delete_entry'), 'nessuno strumento di cancellazione via MCP');
console.log('ok  strumenti MCP:', tools.join(', '));

const call = async (name, args = {}) => JSON.parse((await client.callTool({ name, arguments: args })).content[0].text);
assert.equal((await call('get_profile')).name, 'Emanuele Ielmini');
const rank = await call('rank_for_offer', { offer_text: 'Cerchiamo un DevOps junior: Docker, nginx, CI/CD con GitHub Actions, test di carico e scalabilità, Linux.' });
console.log('    prime voci per un\'offerta DevOps:', rank.ranked.slice(0, 4).map((r) => `${r.entry.title.slice(0, 38)} (${r.score})`).join(' | '));
assert.ok(rank.ranked.length >= 3);
assert.ok(rank.ranked.slice(0, 5).some((r) => /Framasoft|Inception|Sistemi/.test(r.entry.title)), 'voci DevOps in testa');
const s = await call('search_entries', { query: 'Kubernetes' });
assert.equal(s[0].entry.id, id);
const added = await call('add_entry', { type: 'achievement', title: 'Prova da MCP' });
assert.equal(added.title, 'Prova da MCP');
const upd2 = await call('update_entry', { id: added.id, result: 'ok' });
assert.equal(upd2.result, 'ok');
const noTags = await call('get_entry', { id: added.id });
assert.deepEqual(noTags.tags, []);
await client.close();
console.log('ok  MCP: profilo, ricerca, rank_for_offer, aggiunta, modifica');

// 7) Limite di tentativi sbagliati (stesso IP)
let last = 0;
for (let i = 0; i < 12; i++) last = (await j('/api/check', { headers: { Authorization: 'Bearer x' + i } })).status;
assert.equal(last, 429);
assert.equal((await j('/api/check', { headers: auth })).status, 429, 'anche la password giusta è bloccata durante il blocco');
console.log('ok  blocco dopo troppi tentativi sbagliati');

// 8) I dati restano dopo un riavvio
const again = new (await import('./store.js')).Store(dir);
assert.ok(again.get(id), 'dati persistiti su file');
console.log('ok  persistenza su file');

server.close();
fs.rmSync(dir, { recursive: true, force: true });
console.log('\nTUTTI I COLLAUDI SUPERATI');
