// Archivio dati: un solo file JSON, scritto in modo atomico (file temporaneo + rinomina).
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { z } from 'zod';
import { SEED_PROFILE, SEED_ENTRIES } from './seed.js';

export const TYPES = ['experience', 'project', 'hackathon', 'achievement', 'education', 'skill', 'language'];

const httpUrl = z
  .string()
  .max(500)
  .refine((v) => v === '' || /^https?:\/\//i.test(v), 'Il link deve iniziare con http:// o https://');

export const entryFields = {
  type: z.enum(TYPES),
  title: z.string().trim().min(1).max(200),
  org: z.string().trim().max(200).default(''),
  period: z.string().trim().max(100).default(''),
  description: z.string().trim().max(4000).default(''),
  result: z.string().trim().max(2000).default(''),
  tags: z.array(z.string().trim().min(1).max(50)).max(40).default([]),
  link: httpUrl.default(''),
  note: z.string().trim().max(1000).default(''),
};
export const EntrySchema = z.object(entryFields);
export const EntryPatchSchema = z.object(entryFields).partial();

export const ProfileSchema = z.object({
  name: z.string().trim().max(200).default(''),
  headline: z.string().trim().max(300).default(''),
  location: z.string().trim().max(200).default(''),
  email: z.string().trim().max(200).default(''),
  phone: z.string().trim().max(100).default(''),
  links: z.array(z.string().trim().max(300)).max(20).default([]),
  notes: z.string().trim().max(3000).default(''),
});

export class Store {
  constructor(dir) {
    this.dir = dir;
    this.file = path.join(dir, 'cvbase.json');
    fs.mkdirSync(dir, { recursive: true });
    if (fs.existsSync(this.file)) {
      this.data = JSON.parse(fs.readFileSync(this.file, 'utf8'));
    } else {
      const now = new Date().toISOString();
      this.data = {
        profile: ProfileSchema.parse(SEED_PROFILE),
        entries: SEED_ENTRIES.map((e) => ({ id: crypto.randomUUID(), ...EntrySchema.parse(e), createdAt: now, updatedAt: now })),
      };
      this.save();
    }
  }

  save() {
    const tmp = this.file + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(this.data, null, 2));
    fs.renameSync(tmp, this.file);
  }

  list(type) {
    return this.data.entries.filter((e) => !type || e.type === type);
  }
  get(id) {
    return this.data.entries.find((e) => e.id === id) || null;
  }
  add(input) {
    const now = new Date().toISOString();
    const entry = { id: crypto.randomUUID(), ...EntrySchema.parse(input), createdAt: now, updatedAt: now };
    this.data.entries.push(entry);
    this.save();
    return entry;
  }
  update(id, patch) {
    const entry = this.get(id);
    if (!entry) return null;
    Object.assign(entry, EntryPatchSchema.parse(patch), { updatedAt: new Date().toISOString() });
    this.save();
    return entry;
  }
  remove(id) {
    const i = this.data.entries.findIndex((e) => e.id === id);
    if (i < 0) return false;
    this.data.entries.splice(i, 1);
    this.save();
    return true;
  }
  getProfile() {
    return this.data.profile;
  }
  setProfile(p) {
    this.data.profile = ProfileSchema.parse(p);
    this.save();
    return this.data.profile;
  }
  export() {
    return this.data;
  }
  import(obj) {
    const profile = ProfileSchema.parse(obj.profile ?? {});
    const now = new Date().toISOString();
    const entries = (obj.entries ?? []).map((e) => ({
      id: typeof e.id === 'string' && e.id ? e.id : crypto.randomUUID(),
      ...EntrySchema.parse(e),
      createdAt: e.createdAt || now,
      updatedAt: now,
    }));
    this.data = { profile, entries };
    this.save();
  }
}

// ---- Ricerca semplice per parole chiave (nessun servizio esterno) ----
const STOP = new Set(
  ('il lo la i gli le un una di del della dei delle da in con su per tra fra e ed o ma che non si al allo alla ai agli alle ' +
    'le la les des du de un une et ou dans pour avec sur par au aux en ce cette ' +
    'the a an of to in and or for with on at by from is are be as we you our your will can').split(' '),
);

export function tokenize(text) {
  return String(text || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .split(/[^a-z0-9+#.]+/)
    .map((t) => t.replace(/^[.]+|[.]+$/g, ''))
    .filter((t) => t && (t.length >= 2 || t === 'c') && !STOP.has(t));
}

export function scoreEntry(entry, terms) {
  const tagTokens = new Set(entry.tags.flatMap(tokenize));
  const titleTokens = new Set(tokenize(entry.title + ' ' + entry.org));
  const bodyTokens = new Set(tokenize(entry.description + ' ' + entry.result));
  let score = 0;
  const matched = [];
  for (const t of terms) {
    let s = 0;
    if (tagTokens.has(t)) s += 3;
    if (titleTokens.has(t)) s += 2;
    if (bodyTokens.has(t)) s += 1;
    if (s) {
      score += s;
      matched.push(t);
    }
  }
  return { score, matched };
}

export function search(entries, query, { type, limit = 10 } = {}) {
  const terms = [...new Set(tokenize(query))];
  return entries
    .filter((e) => !type || e.type === type)
    .map((e) => ({ entry: e, ...scoreEntry(e, terms) }))
    .filter((r) => r.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);
}
