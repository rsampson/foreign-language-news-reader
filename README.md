# French News Reader

Learn French by reading the day's news. The app shows the top 10 stories from
Le Monde as short summaries, French on the left and English on the right, and
links the two languages sentence by sentence and word by word. Any other web
page can be read the same way.

![The app with a sentence highlighted in both languages, its words coloured by part of speech, and one matching word pair marked](screenshot.png)

## Starting the app

From the applications menu, search for **French News Reader**.

Or from a terminal, in the folder containing the app:

```bash
python3 news_reader.py
```

The first launch of the day fetches and summarises the news, which takes about
3 minutes with Claude. After that the day's stories are saved, so reopening is
instant.

## Reading

| Do this | What happens |
|---|---|
| Move the mouse over a sentence | That sentence and its translation in the other panel are highlighted. The other panel scrolls if needed. |
| Look at the highlighted sentence | Each word is coloured by its part of speech. The key at the bottom of the window explains the colours. |
| Move the mouse over a word | The word and the word or words that translate it turn into dark boxes. A word with no counterpart highlights on its own side only. |
| Click the red ► before a French sentence | The sentence is read aloud in French. Clicking another ► interrupts it. |
| Click **Refresh** | The news, or the web page on screen, is fetched again, replacing today's saved copy. |

Everything works from either panel: you can hover the English to find the
French, or the other way round.

## Reading any web page

The app opens on the news. To read something else, paste a web address into
the **Web page** box and press Enter or click **Read this page**. Click
**Back to Le Monde news** to return to the news.

- The page can be in any language. The AI divides it into up to 10 sections,
  each with a French headline, a short French summary and its English
  translation.
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

## Choosing the AI (Settings)

Click **Settings** to choose which AI writes the summaries and translations.

- **Claude** (default) uses the `claude` command-line tool and your Claude
  subscription. Best quality; supports every feature.
- **Ollama** uses a model running on this computer. Free and offline, but slow
  without a graphics card (around 10 minutes for ten stories with `gemma4`).
- **OpenAI-compatible service** covers OpenAI, Mistral, Groq, OpenRouter and
  others. Enter the service's address, a model name and your API key.

**Word detail** controls the part-of-speech colours and word-to-word matching.
Turn it off for an AI that is too slow or unreliable to produce them. If an AI
returns no word information, the colour key and word highlighting disappear on
their own; sentence highlighting, translation and speech keep working.

"Save and refresh now" fetches the news immediately with the new AI. "Save"
waits until you next click Refresh. The status bar at the top shows which AI
wrote the stories on screen.

The API key is stored in plain text in `settings.json`, readable only by your
user account.

## Things to know

- Summaries are written from Le Monde's headline and short blurb only, not the
  full article, so they are brief.
- The translations, part-of-speech tags and word matches come from the AI. They
  are usually right, but an occasional one will be debatable.
- Speech takes about a second to start, because the audio is generated when you
  click.

## Files

| Path | Purpose |
|---|---|
| `news_reader.py` | The whole app. |
| `settings.json` | Your AI choice, created when you first save Settings. |
| `cache/` | Saved stories: one file per day for the news and one per web page per day. Safe to delete. |
| `.venv/` | Piper, the program that produces the French voice. |
| `voices/` | The French voice model (`fr_FR-siwis-medium`, about 63 MB). |

The app itself needs only Python 3 with Tkinter. If `.venv/` or `voices/` is
missing, speech falls back to the system's robotic `spd-say` voice. To restore
the natural voice, run these in the app folder:

```bash
python3 -m venv .venv
.venv/bin/pip install piper-tts
.venv/bin/python -m piper.download_voices --data-dir voices fr_FR-siwis-medium
```

## Changing things

The constants at the top of `news_reader.py` control:

- `FEED_URL` and `FEED_NAME`: the news source (any RSS feed in French).
- `ITEM_COUNT`: how many stories to show, and the most sections made from a
  web page.
- `MAX_PAGE_CHARS`: how much of a web page's text is given to the AI.
- `PIPER_VOICE` and `PIPER_LENGTH_SCALE`: the voice and its speed (above 1 is
  slower).
- `PARTS_OF_SPEECH`: the colours and labels in the key.
