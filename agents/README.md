# CV Agents: il tuo CV su misura per ogni offerta

Costruisce un CV per una specifica offerta di lavoro usando **solo fatti veri su di te**, salvati in un archivio personale sul tuo computer. Funziona con Claude (Claude Code o chiave API) oppure con un modello locale gratuito, senza chiavi.

## Avvio rapido

Serve [uv](https://docs.astral.sh/uv/) (installa Python da solo). Per il PDF serve Chromium o Chrome; per leggere CV in PDF serve `pdftotext` (poppler). Il Word non richiede nulla.

```sh
git clone https://github.com/Emanuelee00/cv_manager.git
cd cv_manager/agents
uv run cvagents doctor      # cosa hai e cosa manca
uv run cvagents start       # percorso guidato
```

### Hai Claude Code? Fai tutto nella chat

Apri la cartella `cv_manager` in Claude Code (terminale o pannello di VS Code) e scrivi:

```
/cv-start
```

Claude ti fa le domande, legge il tuo CV, collega GitHub, costruisce il CV per l'offerta, te lo **mostra in anteprima** e, quando confermi, crea il **PDF o il Word**. Nessuna chiave da configurare.

### Dal terminale: `cvagents start`

Ti chiede, un passo alla volta:

1. **Quale AI usare.** Tre scelte, sempre visibili con il loro stato:
   - **Claude Code**: usa il tuo login, nessuna chiave;
   - **Claude con chiave API**: la chiave si incolla nascosta e non viene mai salvata su disco;
   - **Modello locale gratuito**: il programma sceglie un modello Qwen3 adatto alla tua RAM, ti dice quanto pesa e lo scarica con Ollama. I dati restano sul computer.
2. **I tuoi dati**: nome, titolo, città, contatti; età, cittadinanza, patente e foto sono facoltativi.
3. **Il tuo CV** (PDF, Word, testo o incollato): l'AI ne estrae le voci e **tu scegli quali tenere**. Nulla viene salvato senza il tuo ok.
4. **GitHub**: con la CLI `gh` (anche repo privati), solo repo pubblici, o niente.
5. **L'offerta e il formato**: PDF, Word o entrambi.

Alla fine ti mostra le scelte salvate e **il comando per far partire tutto**:

```sh
uv run cvagents run                 # usa l'offerta salvata
uv run cvagents run altra.txt       # stessa configurazione, altra offerta
```

Prima di creare i file vedi un'**anteprima** nel terminale e confermi.

## Claude o modello locale?

| | Modello locale (Ollama) | Claude |
|---|---|---|
| Costo | gratis | il tuo abbonamento o a consumo |
| Privacy | tutto resta sul computer | i testi vanno al servizio |
| Qualità | sicura sui fatti, semplice nello stile | molto migliore |
| Flusso | **lite**: il codice sceglie le voci, l'AI traduce e scrive il profilo, la valutazione la fa il codice | **completo**: recruiter e manager separati, fino a 3 giri di miglioramento, humanizer |

Con il modello locale, sezioni, titoli e date vengono dal tuo archivio e ogni traduzione è accettata solo se numeri e link restano identici; le voci tradotte sono segnate nell'anteprima, da rileggere. Più il modello è grande (più RAM), migliore è il testo.

## Senza sudo (computer condivisi, scuola)

`uv run cvagents doctor --install-here ~/ollama --pull` scarica Ollama e il modello in una cartella tua (Linux). Per mettere i modelli altrove: `--models-dir /percorso/con/spazio`. Un modello pesa da 1,4 a 9 GB.

## Comandi

| Comando | Cosa fa |
|---|---|
| `cvagents doctor` | RAM, modello consigliato, Ollama, Claude |
| `cvagents start` | percorso guidato, salva le scelte |
| `cvagents run [offerta.txt]` | rilancia tutto con le scelte salvate |
| `cvagents cv <offerta.txt> --format pdf docx` | CV scegliendo l'AI al momento |
| `cvagents search "parole"` / `show <id>` | cerca e legge il tuo archivio |
| `cvagents add <tipo> <titolo> <testo>` | aggiunge una voce a mano |
| `cvagents exclude <id>` (`--undo`) | non usare mai (o di nuovo) una voce |
| `cvagents github-sync` / `github-public <utente>` | legge i tuoi repo |
| `cvagents build <cv.json> --format pdf docx` | file da un CV già pronto (usato da `/cv-start`) |

## Privacy

Archivio, scelte, foto e file creati stanno in `agents/data/` e `agents/output/`, che **non finiscono su git**. Le chiavi API non vengono mai scritte su disco.

## Test

```sh
uv run python -m unittest discover -s tests -t .
```
