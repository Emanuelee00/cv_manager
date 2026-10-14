// CV Base — un solo servizio: pagina web (per te) + server MCP (per l'assistente).
//
// Variabili d'ambiente OBBLIGATORIE (il server non parte se mancano o sono troppo corte):
//   APP_PASSWORD  password della pagina web (almeno 10 caratteri)
//   MCP_SECRET    chiave segreta nell'indirizzo MCP (almeno 24 caratteri, casuale)
// Opzionali:
//   DATA_DIR  cartella dei dati (default ./data; su Railway usa il volume, es. /data)
//   PORT      porta (default 3000)
import express from 'express';
import crypto from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { z } from 'zod';
import { Store, TYPES, entryFields, EntrySchema, EntryPatchSchema, ProfileSchema, search, tokenize, scoreEntry } from './store.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export function createApp({ appPassword, mcpSecret, dataDir }) {
  if (!appPassword || appPassword.length < 10) throw new Error('APP_PASSWORD mancante o più corta di 10 caratteri.');
  if (!mcpSecret || mcpSecret.length < 24) throw new Error('MCP_SECRET mancante o più corta di 24 caratteri.');

  const store = new Store(dataDir);
  const app = express();
  app.disable('x-powered-by');
  app.set('trust proxy', 1); // Railway/Vercel mettono un proxy davanti

  // Intestazioni di sicurezza. Gli script stanno in file separati, quindi niente script inline.
  app.use((req, res, next) => {
    res.set({
      'Content-Security-Policy': "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
      'X-Content-Type-Options': 'nosniff',
      'Referrer-Policy': 'no-referrer',
      'Cache-Control': 'no-store',
    });
    next();
  });

  const eq = (a, b) => {
    const ha = crypto.createHash('sha256').update(String(a)).digest();
    const hb = crypto.createHash('sha256').update(String(b)).digest();
    return crypto.timingSafeEqual(ha, hb);
  };

  // ---------- Pagina web e API (protette da password) ----------
  const fails = new Map(); // ip -> { n, until }
  const LIMIT = 10;
  const WINDOW_MS = 15 * 60 * 1000;

  function requireAuth(req, res, next) {
    const ip = req.ip;
    const f = fails.get(ip);
    if (f && f.n >= LIMIT && Date.now() < f.until) return res.status(429).json({ error: 'Troppi tentativi. Riprova tra qualche minuto.' });
    const m = /^Bearer (.+)$/.exec(req.get('authorization') || '');
    if (m && eq(m[1], appPassword)) {
      fails.delete(ip);
      return next();
    }
    const cur = f && Date.now() < f.until ? f : { n: 0, until: Date.now() + WINDOW_MS };
    cur.n += 1;
    fails.set(ip, cur);
    return res.status(401).json({ error: 'Password non valida.' });
  }

  const api = express.Router();
  api.use(express.json({ limit: '2mb' }));
  api.use(requireAuth);

  const wrap = (fn) => (req, res) => {
    try {
      fn(req, res);
    } catch (e) {
      if (e instanceof z.ZodError) return res.status(400).json({ error: 'Dati non validi', details: e.issues.map((i) => `${i.path.join('.')}: ${i.message}`) });
      console.error(e);
      res.status(500).json({ error: 'Errore interno' });
    }
  };

  api.get('/check', (req, res) => res.json({ ok: true }));
  api.get('/entries', wrap((req, res) => res.json({ types: TYPES, entries: store.list(req.query.type) })));
  api.post('/entries', wrap((req, res) => res.status(201).json(store.add(req.body))));
  api.put('/entries/:id', wrap((req, res) => {
    const e = store.update(req.params.id, req.body);
    return e ? res.json(e) : res.status(404).json({ error: 'Non trovata' });
  }));
  api.delete('/entries/:id', wrap((req, res) => (store.remove(req.params.id) ? res.json({ ok: true }) : res.status(404).json({ error: 'Non trovata' }))));
  api.get('/profile', wrap((req, res) => res.json(store.getProfile())));
  api.put('/profile', wrap((req, res) => res.json(store.setProfile(req.body))));
  api.get('/export', wrap((req, res) => res.json(store.export())));
  api.post('/import', wrap((req, res) => {
    store.import(req.body);
    res.json({ ok: true, entries: store.list().length });
  }));
  app.use('/api', api);
  app.use('/api', (req, res) => res.status(404).json({ error: 'Non trovato' }));

  app.use(express.static(path.join(__dirname, 'public'), { index: 'index.html', extensions: ['html'] }));

  // ---------- Server MCP (indirizzo segreto: /mcp/<MCP_SECRET>) ----------
  const text = (obj) => ({ content: [{ type: 'text', text: typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2) }] });
  const compact = (e) => ({ id: e.id, type: e.type, title: e.title, org: e.org, period: e.period, tags: e.tags });

  function buildMcp() {
    const server = new McpServer({ name: 'cv-base', version: '1.0.0' });
    const ro = { readOnlyHint: true, destructiveHint: false, openWorldHint: false };

    server.registerTool(
      'get_profile',
      { description: "Dati personali di base (nome, contatti, link, note). Usali per l'intestazione del CV.", annotations: ro },
      async () => text(store.getProfile()),
    );

    server.registerTool(
      'list_entries',
      {
        description: `Elenca le esperienze, i progetti, gli hackathon, i riconoscimenti, la formazione, le competenze e le lingue. Tipi: ${TYPES.join(', ')}. Restituisce la versione completa di ogni voce.`,
        inputSchema: { type: z.enum(TYPES).optional().describe('Filtra per tipo') },
        annotations: ro,
      },
      async ({ type }) => text(store.list(type)),
    );

    server.registerTool(
      'search_entries',
      {
        description: 'Cerca nelle voci per parole chiave (titolo, organizzazione, descrizione, risultato, tag). Restituisce le voci con punteggio e parole trovate.',
        inputSchema: {
          query: z.string().min(1).max(500),
          type: z.enum(TYPES).optional(),
          limit: z.number().int().min(1).max(30).default(10),
        },
        annotations: ro,
      },
      async ({ query, type, limit }) => text(search(store.list(), query, { type, limit }).map((r) => ({ score: r.score, matched: r.matched, entry: r.entry }))),
    );

    server.registerTool(
      'rank_for_offer',
      {
        description:
          "Dato il testo di un'offerta di lavoro, ordina le voci dell'archivio per pertinenza (parole chiave in comune). È solo un aiuto: decidi tu cosa includere nel CV, e non inventare mai numeri o fatti che non sono nelle voci.",
        inputSchema: { offer_text: z.string().min(10).max(20000), limit: z.number().int().min(1).max(30).default(12) },
        annotations: ro,
      },
      async ({ offer_text, limit }) => {
        const terms = [...new Set(tokenize(offer_text))];
        const ranked = store
          .list()
          .map((e) => ({ entry: e, ...scoreEntry(e, terms) }))
          .filter((r) => r.score > 0)
          .sort((a, b) => b.score - a.score)
          .slice(0, limit)
          .map((r) => ({ score: r.score, matched: r.matched, entry: r.entry }));
        return text({ offer_terms: terms.length, ranked });
      },
    );

    server.registerTool(
      'get_entry',
      { description: 'Restituisce una voce completa dal suo id.', inputSchema: { id: z.string() }, annotations: ro },
      async ({ id }) => {
        const e = store.get(id);
        return e ? text(e) : { isError: true, content: [{ type: 'text', text: 'Voce non trovata.' }] };
      },
    );

    server.registerTool(
      'add_entry',
      {
        description: "Aggiunge una nuova voce all'archivio (solo informazioni vere, dette dall'utente).",
        inputSchema: entryFields,
        annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: false },
      },
      async (input) => text(store.add(input)),
    );

    server.registerTool(
      'update_entry',
      {
        description: 'Modifica alcuni campi di una voce esistente. Non cancella voci: la cancellazione si fa solo dalla pagina web.',
        inputSchema: { id: z.string(), ...Object.fromEntries(Object.entries(entryFields).map(([k, v]) => [k, v.optional()])) },
        annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: true, openWorldHint: false },
      },
      async ({ id, ...patch }) => {
        const e = store.update(id, EntryPatchSchema.parse(patch));
        return e ? text(e) : { isError: true, content: [{ type: 'text', text: 'Voce non trovata.' }] };
      },
    );

    return server;
  }

  app.post('/mcp/:key', express.json({ limit: '1mb' }), async (req, res) => {
    if (!eq(req.params.key, mcpSecret)) return res.status(404).end(); // 404, non 401: non riveliamo che esiste
    const server = buildMcp();
    const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
    res.on('close', () => {
      transport.close();
      server.close();
    });
    try {
      await server.connect(transport);
      await transport.handleRequest(req, res, req.body);
    } catch (e) {
      console.error('MCP error:', e.message);
      if (!res.headersSent) res.status(500).json({ jsonrpc: '2.0', error: { code: -32603, message: 'Internal error' }, id: null });
    }
  });
  app.all('/mcp/:key', (req, res) => {
    if (!eq(req.params.key, mcpSecret)) return res.status(404).end();
    res.status(405).set('Allow', 'POST').json({ jsonrpc: '2.0', error: { code: -32000, message: 'Method not allowed.' }, id: null });
  });

  app.use((req, res) => res.status(404).end());
  return { app, store };
}

// Avvio normale (non durante i test)
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const { app } = createApp({
      appPassword: process.env.APP_PASSWORD,
      mcpSecret: process.env.MCP_SECRET,
      dataDir: process.env.DATA_DIR || path.join(__dirname, 'data'),
    });
    const port = Number(process.env.PORT) || 3000;
    app.listen(port, '0.0.0.0', () => console.log(`CV Base in ascolto sulla porta ${port}`));
  } catch (e) {
    console.error('Errore di avvio:', e.message);
    process.exit(1);
  }
}
