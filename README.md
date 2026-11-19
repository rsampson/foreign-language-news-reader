# Foreign Language News Reader

Learn French or Spanish by reading the day's news. The app shows the top 10
stories from Le Monde (French) or El País (Spanish) as short summaries, the
language you are learning on the left and English on the right, and links the
two languages sentence by sentence and word by word. Any other web page can be
read the same way.

![The app with a sentence highlighted in both languages, its words coloured by part of speech, and one matching word pair marked](screenshot.png)

## Download and install

Get the file for your computer from the
[Releases page](../../releases/latest). No Python or other setup is needed.

- **Windows:** run `foreign-language-news-reader-windows-setup.exe`. Windows may say
  "Windows protected your PC" because the app is not signed with a paid
  certificate: click **More info**, then **Run anyway**.
- **Mac:** unzip and drag **Foreign Language News Reader** into Applications. The first
  time, macOS will refuse to open it: open **System Settings > Privacy &
  Security** and click **Open Anyway**. Use the `apple-silicon` file for Macs
  from 2020 onward, `intel` for older ones.
- **Linux:** unpack the `.tar.gz` and run `./install.sh` inside it. This adds
  the app to your menu and a `foreign-language-news-reader` command. `./install.sh
  --uninstall` removes it.

On first launch the app asks you to choose an AI service and paste an API key
from it. The service bills you for what you use; a day's news typically costs
a few cents.

## Privacy and security

- Your API key is stored as plain text in the app's settings file on your own
  computer and is sent only to the AI service you chose.
- The news text, and the text of any web page you load, is sent to that AI
  service. Web pages are fetched directly from your computer.
- The app has no accounts, analytics or telemetry.
- The downloads are built by GitHub from this repository's source
  (`.github/workflows/release.yml`). They are not code-signed.

## Run from source

For people comfortable with Python (3.10 or later, with Tkinter):

```bash
git clone https://github.com/rsampson/foreign-language-news-reader.git
cd foreign-language-news-reader
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m piper.download_voices --data-dir voices fr_FR-siwis-medium
.venv/bin/python news_reader.py
```

On Windows use `.venv\Scripts\python` in place of `.venv/bin/python`. The
packages are optional: without them the app still runs with plain `python3
news_reader.py`, minus the voices and the Claude API-key option.
`python news_reader.py --self-test` checks that everything is in place.

The first launch of the day fetches and summarises the news, which takes a few
minutes. After that the day's stories are saved, so reopening is instant.

## Reading

| Do this | What happens |
|---|---|
| Choose a **Language** | Français or Español, at the top left. The app fetches that language's news (or the web page on screen) and remembers the choice. |
| Move the mouse over a sentence | That sentence and its translation in the other panel are highlighted. The other panel scrolls if needed. |
| Look at the highlighted sentence | Each word is coloured by its part of speech. The key at the bottom of the window explains the colours. |
| Move the mouse over a word | The word and the word or words that translate it turn into dark boxes. A word with no counterpart highlights on its own side only. |
| Click the red ► before a sentence | The sentence is read aloud in French or Spanish. Clicking another ► interrupts it. |
| Right-click a word in the left panel | Just that word is read aloud, and it and its translation are highlighted. On a Mac, Control-click works too. |
| Listen to a sentence | Each word is highlighted in orange and underlined as it is spoken, together with its translation in the other panel. The timing is estimated from the recording, so it can be a syllable early or late. |
| Choose a **Speech speed** | Sets how fast sentences are read aloud: Normal, Slow (the default), Slower or Very slow. The choice is remembered. |
| Click **Refresh** | The news, or the web page on screen, is fetched again, replacing today's saved copy. |

Everything works from either panel: you can hover the English to find the
French or Spanish, or the other way round.

**The Spanish voice downloads the first time you choose Spanish** (about
60 MB, once). Progress shows next to **ESPAÑOL** above the left panel; you can
read while it downloads, and the ► buttons work as soon as it finishes. The
download is checked against a fixed checksum before it is used. The French
voice is built in.

## Reading any web page

The app opens on the news. To read something else, paste a web address into
the **Web page** box and press Enter or click **Read this page**. Click
**Back to Le Monde news** (or **El País**) to return to the news.

- The page can be in any language. The AI divides it into up to 10 sections,
  each with a headline and a short summary in the language you chose, plus
  their English translation.
- It is a summary, not the whole page: only the first 12,000 characters of the
  page's readable text are used, so long pages are covered from the top.
- Clutter is filtered out before the AI sees the page: menus, headers and
  footers, and anything the page labels as an advert, sponsored content, a
  cookie notice, a newsletter sign-up, a pop-up or a "related stories" box.
  Scripts are never run, so adverts inserted by scripts never load at all.
  Promotional text written as ordinary paragraphs can still slip through.
- Pages that need a login, or that build their content with JavaScript, give a
  "No readable text found" message. PDFs and other files are not supported.
- Each page is saved for the day, so loading the same address again is instant.

## Translating your own English

Click **Translate…** at the top right to open a separate window for
practising with your own sentences.

1. Type or paste English into the top box (up to 2,000 characters).
2. Choose **Français** or **Español** next to **Into:**. It starts on the
   language you are reading.
3. Click **Translate**, or press Ctrl+Enter. The translation appears below,
   usually within about ten seconds.
4. Click **► Listen** to hear it at your chosen speech speed, or **Copy** to
   put it on the clipboard.

Both boxes have the right-click Cut, Copy and Paste menu and Ctrl+A. The window
can stay open beside the news; clicking **Translate…** again brings it to the
front. Each translation uses the AI service chosen in Settings, so it counts
towards that service's usage like the news does.

## Do I need an API key?

Not if you already use Claude Code. The app can reach an AI in two ways that
are billed differently:

- **With a Claude Pro or Max subscription and no key.** If the Claude Code
  command-line tool is installed and signed in on your computer, the app finds
  it and uses it automatically; you are never asked for a key. Each time the
  news is fetched, it uses some of your subscription's allowance, the same
  pool your Claude Code sessions draw from. To switch to it on a computer
  where the welcome screen appeared, click **Other options…** (or
  **Settings**) and choose **Claude Code command-line tool**.
- **With an API key.** For everyone else. A key comes from a separate
  developer account with an AI service and is billed per use, typically a few
  cents for a day's news. A Claude Pro or Max subscription does not include an
  API key; they are separate products.

Either way, the day's stories are saved after the first fetch, so the AI is
used once per day unless you click **Refresh** or load a web page.

## Trying it for free with a local model

If you are curious about the app and not ready to open an account with an AI
service, you can try it with a model that runs on your own computer through
[Ollama](https://ollama.com). It costs nothing and nothing leaves your
computer.

> **Caution: this is for a trial, not for everyday use.** A local model is
> far slower than an AI service. How long a fetch takes depends entirely on
> your hardware. On a desktop computer without a graphics card, two stories
> took about two minutes in testing, so expect ten minutes or more for the
> day's ten stories, and possibly much longer on a laptop or older machine.
> The summaries and translations are also less reliable.

1. Install Ollama from [ollama.com](https://ollama.com).
2. Download a model. Gemma 4 is a reasonable choice; it is a download of
   about 10 GB and needs a computer with plenty of memory:

   ```bash
   ollama pull gemma4
   ```

3. Start the app. On the welcome screen click **Other options…** (or click
   **Settings** if the app is already set up).
4. Choose **Ollama (model running on this computer)**. Leave the address as
   it is and set the model to `gemma4:latest`.
5. Untick **Word detail**. A local model is unlikely to produce the
   part-of-speech colours and word-to-word matching reliably, and asking for
   them makes it slower still. You still get sentence highlighting,
   translation and speech.
6. Click **Save and refresh now** and wait. The status line at the top says
   the app is fetching until it finishes; the **Refresh** button stays greyed
   out during that time.

When you are ready for everyday use, switch to one of the options under
[Do I need an API key?](#do-i-need-an-api-key).

## Choosing the AI (Settings)

Click **Settings** to choose which AI writes the summaries and translations.

- **Claude, with an Anthropic API key.** Paste a key from
  platform.claude.com. Uses Claude Opus by default; supports every feature.
- **OpenAI-compatible service, with an API key.** Covers OpenAI, Google
  Gemini, Mistral, Groq, OpenRouter and others. Enter the service's address
  and your key, click **List models** and pick one.
- **Ollama** uses a model running on your own computer. Free and offline, but
  slow without a graphics card (around 10 minutes for ten stories).
- **Claude Code command-line tool**, for people who have it installed. It uses
  a Claude subscription instead of an API key.

**Word detail** controls the part-of-speech colours and word-to-word matching.
Turn it off for an AI that is too slow or unreliable to produce them. If an AI
returns no word information, the colour key and word highlighting disappear on
their own; sentence highlighting, translation and speech keep working.

"Save and refresh now" fetches the news immediately with the new AI. "Save"
waits until you next click Refresh. The status bar at the top shows which AI
wrote the stories on screen.

API keys are stored in plain text in the settings file, readable only by your
user account.

## Things to know

- Summaries are written from each story's headline and short blurb in the
  news feed only, not the full article, so they are brief.
- The translations, part-of-speech tags and word matches come from the AI. They
  are usually right, but an occasional one will be debatable.
- Speech takes about a second to start, because the audio is generated when you
  click.

## Files

| Path | Purpose |
|---|---|
| `news_reader.py` | The whole app. |
| `settings.json` | Your AI choice, created when you first save Settings. |
| `cache/` | Saved stories: one file per language per day for the news, and one per web page. Safe to delete. |
| `.venv/` | Piper, the program that produces the voices. |
| `voices/` | The voice models: French (`fr_FR-siwis-medium`) and, once downloaded, Spanish (`es_ES-davefx-medium`), about 63 MB each. |

In the downloaded app, settings and the cache live in your user data folder
instead (`%APPDATA%\foreign-language-news-reader`, `~/Library/Application
Support/foreign-language-news-reader` or `~/.local/share/foreign-language-news-reader`).

## Changing things

The constants at the top of `news_reader.py` control:

- `LANGUAGES`: each language's news feed, voice (with its checksums),
  colour-key labels and grammar notes for the AI. Adding a language means
  adding an entry here.
- `ITEM_COUNT`: how many stories to show, and the most sections made from a
  web page.
- `MAX_PAGE_CHARS`: how much of a web page's text is given to the AI.
- `SPEECH_SPEEDS`: the speeds offered in the **Speech speed** box.
- `PARTS_OF_SPEECH`: the colours and labels in the key.

## Licence and credits

Foreign Language News Reader is free software under the [GNU GPL v3](LICENSE), with no
warranty. The downloadable apps include [Piper](https://github.com/OHF-voice/piper1-gpl)
(GPL-3.0) and the `fr_FR-siwis-medium` voice, trained on the SIWIS French
speech dataset (CC BY 4.0). The Spanish voice, `es_ES-davefx-medium`
(CC0), is downloaded from the [Piper voices](https://huggingface.co/rhasspy/piper-voices)
collection when first needed. News summaries are generated from the public RSS
feeds of Le Monde and El País; this project is not affiliated with either.
