# CV Base

Il tuo archivio personale di esperienze, progetti, hackathon, competenze e lingue.
Un solo servizio con due facce:

- **Una pagina web** (la apri dal telefono) dove aggiungi e modifichi le voci, anche **dettandole a voce**.
- **Un server MCP** a cui Claude si collega per leggere le tue voci e scegliere quelle giuste quando scrivi un CV per un'offerta.

Non serve Supabase, né un account utente: sei solo tu. Le protezioni sono due segreti che scegli tu.

## Cosa c'è già dentro

Al primo avvio carica 23 voci prese dai tuoi CV e dai tuoi repository (Chez Marthe, Framasoft, SANS, Inception, esperienze, formazione, competenze…).
Le voci con una nota gialla "DA COMPLETARE" o "DA VERIFICARE" aspettano un tuo dato (per esempio i numeri del sito di Green Village).
Il seed si può cambiare in `seed.js` **prima** del primo avvio; dopo, i dati stanno nel file `cvbase.json` nella cartella dati.

## Provarlo sul tuo computer (2 minuti)

Serve Node 20 o più recente.

```sh
npm install
APP_PASSWORD="scegli-una-password-lunga" MCP_SECRET="$(node -e "console.log(require('crypto').randomBytes(24).toString('hex'))")" npm start
```

Apri http://localhost:3000 ed entra con la password. Per eseguire i collaudi automatici: `npm test`.

## Metterlo online su Railway

Perché Claude possa collegarsi, il server deve essere raggiungibile da internet.

1. Metti questa cartella in un repository GitHub **privato** (oppure usa la riga di comando di Railway).
2. Su railway.com crea un progetto "Deploy from GitHub repo" e scegli il repository. Railway trova il `Dockerfile` e costruisce da solo.
3. **Volume (importante):** aggiungi un Volume al servizio e montalo su `/data`. Senza volume i dati si perdono a ogni nuovo deploy.
4. **Variabili** del servizio:
   - `APP_PASSWORD` = una password lunga (almeno 10 caratteri), quella della pagina web
   - `MCP_SECRET` = una chiave casuale lunga (almeno 24 caratteri). Generala così:
     `node -e "console.log(require('crypto').randomBytes(24).toString('hex'))"`
   - `DATA_DIR` = `/data` (è già il valore predefinito nell'immagine)
5. Nelle impostazioni di rete del servizio genera un dominio pubblico. Avrai un indirizzo tipo `https://nome.up.railway.app`.
6. Il server **non parte** se `APP_PASSWORD` o `MCP_SECRET` mancano o sono troppo corte: è voluto.

I prezzi e le voci del menu di Railway cambiano: controllali al momento del deploy.

## Usarlo dal telefono come un'app (senza APK)

La pagina è un'app installabile (PWA): niente file APK, niente Play Store.

1. Apri `https://nome.up.railway.app` con **Chrome** sul telefono Android.
2. Menu ⋮ → **Installa app** (o "Aggiungi a schermata Home").
3. Si apre a schermo intero con la sua icona, come un'app vera. Serve internet, perché i dati stanno sul server.

Se vuoi proprio un file APK: gratis con [PWABuilder](https://www.pwabuilder.com) (inserisci il tuo indirizzo e scarica il pacchetto Android) oppure con Capacitor in Android Studio. L'APK sarebbe comunque solo un contenitore della stessa pagina.

Dettatura:

- Il bottone 🎤 usa il riconoscimento vocale del browser (va bene su Chrome per Android; su altri browser può non esserci).
- Se non c'è, usa il microfono della tastiera del telefono: funziona in ogni campo di testo.

**Vercel non serve:** la pagina è già servita dallo stesso indirizzo. Metterla su Vercel separatamente richiederebbe di cambiare le impostazioni di sicurezza (la pagina e le API devono stare sullo stesso indirizzo).

## Collegare Claude

Nelle impostazioni dei connettori di Claude aggiungi un connettore personalizzato e incolla questo indirizzo (la chiave è la parte finale):

```
https://nome.up.railway.app/mcp/<il-tuo-MCP_SECRET>
```

Non ho potuto provare il collegamento con la tua app Claude; è provato con il client MCP ufficiale. Se la tua versione di Claude non accetta connettori senza accesso, scrivimelo e passiamo a un login vero (OAuth).

Strumenti che Claude vede: `get_profile`, `list_entries`, `search_entries`, `rank_for_offer` (ordina le voci per un'offerta), `get_entry`, `add_entry`, `update_entry`. **Non può cancellare**: la cancellazione si fa solo dalla pagina web.

Esempio: «Ecco un'offerta DevOps [incolla]. Usa il mio archivio, scegli le voci migliori e scrivi la sezione Projets in francese, senza inventare numeri.»

## Sicurezza, in breve

- **L'indirizzo MCP è una password.** Chi lo ha può leggere (e aggiungere) le tue voci. Non condividerlo e non incollarlo in chat pubbliche. Se trapela: cambia `MCP_SECRET` su Railway e aggiorna il connettore.
- Dopo 10 password sbagliate la pagina si blocca per 15 minuti per quell'indirizzo.
- Non salvare qui password, codici fiscali o documenti: i dati non sono cifrati sul disco.
- Scarica ogni tanto un **Backup** dalla pagina (pulsante "Backup"). Se un giorno perdi il volume, lo reimporti da lì.
- La pagina usa una politica di sicurezza stretta (nessuno script esterno) e mostra tutto come testo.

## File

- `server.js` server web + MCP · `store.js` archivio e ricerca · `seed.js` dati iniziali
- `public/` pagina web · `test.js` collaudi · `Dockerfile` per Railway
