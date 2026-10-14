# CV Agents: il tuo CV su misura per ogni offerta

Costruisce un CV (e in seguito una lettera) per una specifica offerta di lavoro usando **solo fatti veri su di te**, salvati in un archivio personale sul tuo computer. Funziona con un modello locale gratuito (nessuna chiave) oppure con Claude.

## Avvio rapido (5 minuti)

Serve [uv](https://docs.astral.sh/uv/) (un gestore di Python) e Python 3.12 o più recente. Per il PDF serve anche Chromium o Chrome, e `pdftotext` se vuoi leggere CV in PDF.

```sh
git clone https://github.com/Emanuelee00/cv_manager.git
cd cv_manager/agents
uv run cvagents doctor      # controlla cosa hai e cosa manca
uv run cvagents start       # percorso guidato
```

`start` ti chiede:

1. **Quale AI usare.** Se non hai Claude, scegli "Scarica un modello locale": il programma sceglie un modello adatto alla tua RAM, ti dice quanto pesa e lo scarica con una barra di avanzamento. Gratis, senza chiavi, i dati restano sul tuo computer.
2. **I tuoi dati**: nome, titolo, città, contatti. Età, cittadinanza, patente e foto sono facoltativi.
3. **Il tuo CV** (file PDF, Word o testo, oppure incollato): l'AI ne estrae le voci e tu scegli quali tenere. Nulla viene salvato senza il tuo ok.
4. **GitHub** (facoltativo): legge i tuoi repo pubblici, senza chiavi.

Poi, per ogni offerta:

```sh
uv run cvagents cv offerta.txt        # offerta salvata in un file di testo
```

Il programma scrive il CV, ti fa le domande se gli manca qualcosa, lo valuta, ti propone miglioramenti e produce un **PDF di una pagina** in `output/`.

## Modello locale o Claude?

| | Modello locale (Ollama) | Claude |
|---|---|---|
| Costo | gratis | a pagamento (o il tuo abbonamento) |
| Privacy | tutto resta sul computer | i testi vengono inviati al servizio |
| Qualità | buona per i fatti, più semplice nello stile | molto migliore |
| Flusso | **lite**: veloce, un giro di miglioramento | **completo**: HR e manager separati, fino a 3 giri, humanizer |

Per usare Claude: `export ANTHROPIC_API_KEY=...` oppure installa Claude Code e fai login: `start` li trova da solo. Con Claude Code aperto in questa cartella puoi anche usare `/cv-loop` e `/letter-flow` (il percorso più completo).

Il modello locale non è perfetto: per questo i controlli sui fatti (numeri, id, ripetizioni, una pagina) li fa il codice, non il modello. Un numero che non compare nel tuo archivio viene segnalato e tolto.

## Senza sudo (computer condivisi, scuola)

`uv run cvagents doctor --install-here ~/ollama --pull` scarica Ollama e il modello in una cartella tua (solo Linux). Per mettere i modelli altrove: `--models-dir /percorso/grande`. Un modello pesa da 1,4 a 9 GB: controlla lo spazio.

## Comandi utili

| Comando | Cosa fa |
|---|---|
| `cvagents doctor` | RAM, modello consigliato, Ollama, Claude |
| `cvagents start` | percorso guidato |
| `cvagents cv <offerta.txt>` | CV per un'offerta |
| `cvagents search "parole"` | cerca nel tuo archivio |
| `cvagents add <tipo> <titolo> <testo>` | aggiunge una voce a mano |
| `cvagents github-sync` | legge i tuoi repo con la CLI `gh` (anche privati) |
| `cvagents render <cv.html>` | HTML a PDF e controllo di una pagina |

## Privacy

Archivio, foto e PDF stanno in `agents/data/` e `agents/output/`, che **non finiscono su git**. Nessun dato personale è nel repository.

## Test

```sh
uv run python -m unittest discover -s tests -t .
```
