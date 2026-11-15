#!/usr/bin/env python3
"""Side-by-side French / English news reader for learning French.

Fetches the top 10 items from Le Monde's front-page RSS feed, asks an AI
(the `claude` CLI by default; Ollama or an OpenAI-compatible service can be
chosen under Settings) for a short French summary of each with a
sentence-by-sentence English translation, and shows them in two panels. Hovering a sentence
highlights it and its counterpart in the other panel, with each word
coloured by its part of speech (see the key at the bottom of the window).
Hovering a word also marks the word or words that translate it. The small
play button before each French sentence reads it aloud, using the Piper
voice in .venv/ and voices/ if present, otherwise spd-say.

The app itself needs only the standard library. Run:  python3 news_reader.py
"""

import datetime
import json
import re
import shutil
import subprocess
import tempfile
import threading
import tkinter as tk
import tkinter.font as tkfont
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

FEED_URL = "https://www.lemonde.fr/rss/une.xml"
FEED_NAME = "Le Monde"
ITEM_COUNT = 10
AI_TIMEOUT_S = 1800  # local models on a CPU can be slow
APP_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = APP_DIR / "settings.json"

# Which AI writes the summaries. Changed from the Settings button and saved
# in settings.json. "openai" is any service speaking the OpenAI chat API
# (OpenAI, Mistral, Groq, OpenRouter, Gemini's compatible endpoint, ...).
PROVIDERS = {
    "claude": "Claude (claude command-line tool)",
    "ollama": "Ollama (model running on this computer)",
    "openai": "OpenAI-compatible service (needs an API key)",
}
DEFAULT_SETTINGS = {
    "provider": "claude",
    # Word detail = parts of speech and word-to-word matching. It needs a
    # strong model; turn it off for an AI that cannot produce it reliably.
    "word_detail": True,
    "claude_model": "sonnet",
    "ollama_url": "http://localhost:11434",
    "ollama_model": "gemma4:latest",
    "openai_url": "https://api.openai.com/v1",
    "openai_model": "",
    "openai_key": "",
}
# Piper neural voice (preferred). Installed in the project's virtualenv:
#   python3 -m venv .venv && .venv/bin/pip install piper-tts
#   .venv/bin/python -m piper.download_voices --data-dir voices fr_FR-siwis-medium
PIPER_PYTHON = APP_DIR / ".venv" / "bin" / "python"
PIPER_VOICE = "fr_FR-siwis-medium"
VOICE_DIR = APP_DIR / "voices"
PIPER_LENGTH_SCALE = 1.15  # above 1 is slower; a little slow for learners
PLAYER = shutil.which("pw-play") or shutil.which("paplay") or shutil.which("aplay")
SPD_SAY_RATE = -20  # fallback voice: -100 (slowest) to 100
SPEAK_GLYPH = "\u25ba"  # the small play button in front of each French sentence
CACHE_DIR = APP_DIR / "cache"

BG = "#fbf9f4"
FG = "#22201c"
MUTED = "#8a8478"
SPEAK_COLOUR = "#b0462f"
HIGHLIGHT = "#efe9da"  # band behind the whole hovered sentence

# Part-of-speech tag -> (key label, background colour for the word).
PARTS_OF_SPEECH = {
    "NOUN":  ("Noun · nom", "#a8d1ff"),
    "PROPN": ("Proper noun · nom propre", "#cdc4ff"),
    "VERB":  ("Verb · verbe", "#ffb3b3"),
    "ADJ":   ("Adjective · adjectif", "#b5e6ad"),
    "ADV":   ("Adverb · adverbe", "#ffcf94"),
    "PRON":  ("Pronoun · pronom", "#f7b6e0"),
    "DET":   ("Article/determiner · déterminant", "#d6d6d6"),
    "PREP":  ("Preposition · préposition", "#fff08a"),
    "CONJ":  ("Conjunction · conjonction", "#9fe3dc"),
    "NUM":   ("Number · nombre", "#dcc3a0"),
}

PROMPT = """\
You are preparing reading material for an English speaker learning French.
Below is a JSON array of news items (title and description) from {feed}.

For EACH item, in the same order, write:
- the headline in French (clean it up: drop prefixes like "EN DIRECT,")
- a summary of 2 to 3 French sentences in clear, natural, standard French,
  based ONLY on the title and description given. Do not add facts.
- a faithful English translation of every French sentence. Keep the
  translation close enough to the French that a learner can match the words,
  while still being correct, natural English.

Each French sentence must pair with exactly one English sentence.
{detail}
Reply with ONLY a JSON array, no prose and no code fence, shaped like:
[{{"sentences": [{example}]}}]
The first pair of each item is the headline. The array must have exactly
{n} elements.

News items:
{items}
"""

EXAMPLE_PLAIN = '{"fr": "headline", "en": "headline"}, {"fr": "...", "en": "..."}'
EXAMPLE_DETAIL = """{"fr": "headline", "en": "headline",
                   "fr_pos": "Le/DET/1 chat/NOUN/2 noir/ADJ/3 dort/VERB/4",
                   "en_pos": "The/DET/1 black/ADJ/3 cat/NOUN/2 sleeps/VERB/4"}"""

PROMPT_DETAIL = """
Also tag the part of speech of every word of every sentence, in both
languages, as a string of word/TAG tokens separated by spaces, in sentence
order. Tags: {tags}. Auxiliary and modal verbs are VERB. Contractions such
as "du" or "au" are PREP. Split French elisions into two tokens
(l’/DET Estonie/PROPN, qu’/CONJ il/PRON) and English possessives likewise.
Leave punctuation out. Spell each word exactly as it appears in the sentence.

Finally, append a link number to every token (word/TAG/N) showing which
words translate each other. Within one sentence pair, a French word and the
English word or words that translate it share the same N, counting from 1
in each pair. A multi-word match shares one number on both sides
(a/VERB/4 annoncé/VERB/4 with announced/VERB/4). A word with no counterpart
in the other language gets 0.
"""


# ---------------------------------------------------------------- data

def fetch_feed():
    """Return the top ITEM_COUNT feed items as dicts with title/description."""
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        root = ET.fromstring(resp.read())
    items = []
    for node in root.iter("item"):
        title = (node.findtext("title") or "").replace("\xa0", " ").strip()
        desc = (node.findtext("description") or "").replace("\xa0", " ").strip()
        if title:
            items.append({"title": title, "description": desc})
        if len(items) == ITEM_COUNT:
            break
    if not items:
        raise RuntimeError("The news feed returned no items.")
    return items


def load_settings():
    settings = dict(DEFAULT_SETTINGS)
    try:
        saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        settings.update({k: v for k, v in saved.items() if k in settings})
    except (OSError, json.JSONDecodeError, AttributeError):
        pass  # no settings yet, or unreadable: use the defaults
    if settings["provider"] not in PROVIDERS:
        settings["provider"] = DEFAULT_SETTINGS["provider"]
    return settings


def save_settings(settings):
    SETTINGS_FILE.touch(mode=0o600, exist_ok=True)  # it may hold an API key
    SETTINGS_FILE.chmod(0o600)
    SETTINGS_FILE.write_text(json.dumps(settings, indent=1), encoding="utf-8")


def ai_label(settings):
    """Short name of the configured AI, for the status bar and the cache."""
    provider = settings["provider"]
    return f"{provider}:{settings[provider + '_model']}"


def ask_claude(prompt, settings):
    try:
        # Run from an empty directory so no project instructions are loaded.
        with tempfile.TemporaryDirectory() as cwd:
            proc = subprocess.run(
                ["claude", "-p", "--model", settings["claude_model"]],
                input=prompt, capture_output=True, text=True,
                timeout=AI_TIMEOUT_S, cwd=cwd)
    except FileNotFoundError:
        raise RuntimeError("The 'claude' command was not found on PATH.")
    except subprocess.TimeoutExpired:
        raise RuntimeError("claude took too long to respond.")
    if proc.returncode != 0:
        raise RuntimeError(
            "claude failed: " + (proc.stderr or proc.stdout).strip()[:400])
    return proc.stdout


def post_json(url, payload, headers=None):
    """POST a JSON payload and return the decoded JSON reply."""
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=AI_TIMEOUT_S) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace").strip()[:300]
        raise RuntimeError(f"{url} answered {exc.code}: {detail}")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Could not reach {url} ({getattr(exc, 'reason', exc)}).")
    except json.JSONDecodeError:
        raise RuntimeError(f"{url} did not answer with JSON.")


def ask_ollama(prompt, settings):
    reply = post_json(
        settings["ollama_url"].rstrip("/") + "/api/generate",
        {"model": settings["ollama_model"], "prompt": prompt, "stream": False,
         # Room for the whole prompt and answer; the default would cut it off.
         "options": {"num_ctx": 16384, "temperature": 0.2}})
    return reply.get("response", "")


def ask_openai(prompt, settings):
    if not settings["openai_model"]:
        raise RuntimeError("No model name is set for the OpenAI-compatible "
                           "service. Open Settings to add one.")
    headers = {}
    if settings["openai_key"]:
        headers["Authorization"] = "Bearer " + settings["openai_key"]
    reply = post_json(
        settings["openai_url"].rstrip("/") + "/chat/completions",
        {"model": settings["openai_model"],
         "messages": [{"role": "user", "content": prompt}]},
        headers)
    try:
        return reply["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("Unexpected reply from the AI service: "
                           + json.dumps(reply)[:300])


ASK = {"claude": ask_claude, "ollama": ask_ollama, "openai": ask_openai}


def summarise(items, settings):
    """Ask the configured AI for paired French/English sentences per item."""
    detail = settings["word_detail"]
    prompt = PROMPT.format(
        feed=FEED_NAME, n=len(items),
        detail=PROMPT_DETAIL.format(tags=", ".join(PARTS_OF_SPEECH))
        if detail else "",
        example=EXAMPLE_DETAIL if detail else EXAMPLE_PLAIN,
        items=json.dumps(items, ensure_ascii=False, indent=1))
    return parse_stories(ASK[settings["provider"]](prompt, settings))


def parse_stories(text):
    """Extract and validate the JSON array of stories from the AI's reply."""
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise RuntimeError("The AI did not return JSON: " + text.strip()[:200])
    try:
        raw = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"The AI returned invalid JSON ({exc}).")
    stories = []
    for entry in raw:
        if not isinstance(entry, dict) or not isinstance(
                entry.get("sentences"), list):
            continue
        pairs = [
            {"fr": p["fr"].strip(), "en": p["en"].strip(),
             "fr_pos": parse_tagged(p.get("fr_pos")),
             "en_pos": parse_tagged(p.get("en_pos"))}
            for p in entry["sentences"]
            if isinstance(p, dict) and isinstance(p.get("fr"), str)
            and isinstance(p.get("en"), str) and p["fr"].strip()
            and p["en"].strip()
        ]
        if pairs:
            stories.append(pairs)
    if not stories:
        raise RuntimeError("The AI returned no usable stories.")
    return stories


def parse_tagged(tagged):
    """Turn "Le/DET/1 chat/NOUN/2" into [["Le", "DET", 1], ["chat", "NOUN", 2]].

    The number links a word to its translation; 0 means no counterpart.
    """
    words = []
    for token in (tagged if isinstance(tagged, str) else "").split():
        parts = token.rsplit("/", 2)
        if len(parts) == 3 and parts[2].isdigit():
            word, pos, link = parts[0], parts[1], int(parts[2])
        else:  # link number missing
            word, _, pos = token.rpartition("/")
            link = 0
        if word and pos.upper() in PARTS_OF_SPEECH:
            words.append([word, pos.upper(), link])
    return words


def locate_words(sentence, words):
    """Yield (start, end, pos, link) spans of tagged words in sentence.

    Words are matched left to right; any that cannot be found are skipped so
    a tagging slip never breaks the display.
    """
    folded = sentence.replace("\u2019", "'").lower()
    cursor = 0
    for word, pos, link in words:
        at = folded.find(word.replace("\u2019", "'").lower(), cursor)
        if at == -1:
            continue
        cursor = at + len(word)
        yield at, cursor, pos, link


_speech_lock = threading.Lock()
_speech_proc = None  # the piper or player process currently running
_speech_turn = 0     # bumped on every request so older ones give up


def piper_available():
    return (PIPER_PYTHON.exists() and PLAYER
            and (VOICE_DIR / f"{PIPER_VOICE}.onnx").exists())


def speech_available():
    return bool(piper_available() or shutil.which("spd-say"))


def _run_speech_step(turn, command):
    """Run one speech subprocess unless a newer request has taken over."""
    global _speech_proc
    with _speech_lock:
        if turn != _speech_turn:
            return False
        _speech_proc = subprocess.Popen(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        proc = _speech_proc
    return proc.wait() == 0


def speak_french(sentence):
    """Read a sentence aloud in French, replacing anything still playing.

    Uses the Piper neural voice when it is installed, otherwise spd-say.
    """
    global _speech_turn
    with _speech_lock:
        _speech_turn += 1
        turn = _speech_turn
        if _speech_proc and _speech_proc.poll() is None:
            _speech_proc.kill()  # stop the previous sentence

    def run():
        if not piper_available():
            subprocess.run(["spd-say", "-C"], capture_output=True)
            _run_speech_step(turn, ["spd-say", "-l", "fr", "-r",
                                    str(SPD_SAY_RATE), "--", sentence])
            return
        with tempfile.TemporaryDirectory() as tmp:
            wav = str(Path(tmp) / "sentence.wav")
            if _run_speech_step(turn, [
                    str(PIPER_PYTHON), "-m", "piper", "-m", PIPER_VOICE,
                    "--data-dir", str(VOICE_DIR),
                    "--length-scale", str(PIPER_LENGTH_SCALE),
                    "-f", wav, "--", sentence]):
                _run_speech_step(turn, [PLAYER, wav])

    threading.Thread(target=run, daemon=True).start()


def cache_path():
    return CACHE_DIR / f"{datetime.date.today().isoformat()}.json"


def load_stories(settings, force=False):
    """Return today's stories, from cache unless force is set.

    The cache is a dict {"ai": label, "stories": [[pair, ...], ...]}.
    """
    path = cache_path()
    if not force and path.exists():
        try:
            cached = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(cached, list):  # cache written before Settings existed
                cached = {"ai": "claude:sonnet", "stories": cached}
            cached["stories"][0][0]["fr"]  # raises if the format is old
            return cached
        except (OSError, json.JSONDecodeError, LookupError, TypeError):
            pass  # unreadable or older cache: fall through and rebuild it
    result = {"ai": ai_label(settings),
              "stories": summarise(fetch_feed(), settings)}
    CACHE_DIR.mkdir(exist_ok=True)
    path.write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return result


# ------------------------------------------------------------------ UI

class NewsReader:
    def __init__(self, root):
        self.root = root
        root.title(f"Lire les nouvelles — {FEED_NAME}")
        root.geometry("1280x820")
        root.configure(bg=BG)

        base = tkfont.nametofont("TkTextFont").actual("family")
        self.body_font = tkfont.Font(family=base, size=13)
        self.head_font = tkfont.Font(family=base, size=16, weight="bold")
        self.label_font = tkfont.Font(family=base, size=10, weight="bold")
        self.key_font = tkfont.Font(family=base, size=10)

        bar = tk.Frame(root, bg=BG)
        bar.pack(fill="x", padx=16, pady=(10, 0))
        self.status = tk.Label(bar, bg=BG, fg=MUTED, font=self.label_font,
                               anchor="w")
        self.status.pack(side="left", fill="x", expand=True)
        self.refresh_btn = tk.Button(bar, text="Refresh", relief="flat",
                                     command=lambda: self.load(force=True))
        self.refresh_btn.pack(side="right")
        tk.Button(bar, text="Settings", relief="flat",
                  command=self.open_settings).pack(side="right", padx=(0, 6))
        self.settings = load_settings()

        self._make_key(root)  # packed at the bottom before the panes expand

        panes = self.panes = tk.Frame(root, bg=BG)
        panes.pack(fill="both", expand=True, padx=8, pady=8)
        panes.columnconfigure(0, weight=1, uniform="pane")
        panes.columnconfigure(1, weight=1, uniform="pane")
        panes.rowconfigure(0, weight=1)
        self.panels = {
            "fr": self._make_panel(panes, 0, "FRANÇAIS"),
            "en": self._make_panel(panes, 1, "ENGLISH"),
        }
        self.active = None  # tag name of the highlighted sentence
        self.active_word = None  # (panel, sentence tag, word number)
        self.french = {}  # sentence tag -> French sentence, for speaking
        # panel -> sentence tag -> [(start index, end index, pos, link), ...]
        self.words = {text: {} for text in self.panels.values()}
        self.load()

    def _make_key(self, root):
        """Legend explaining the part-of-speech colours."""
        key = self.key = tk.Frame(root, bg=BG)
        key.pack(side="bottom", fill="x", padx=24, pady=(0, 10))
        columns = 5
        for i, (label, colour) in enumerate(PARTS_OF_SPEECH.values()):
            cell = tk.Frame(key, bg=BG)
            cell.grid(row=i // columns, column=i % columns, sticky="w",
                      padx=(0, 22), pady=2)
            tk.Label(cell, bg=colour, width=2).pack(side="left")
            tk.Label(cell, text=label, bg=BG, fg=FG,
                     font=self.key_font).pack(side="left", padx=(6, 0))

    def _make_panel(self, parent, column, label):
        frame = tk.Frame(parent, bg=BG)
        frame.grid(row=0, column=column, sticky="nsew", padx=8)
        tk.Label(frame, text=label, bg=BG, fg=MUTED, font=self.label_font,
                 anchor="w").pack(fill="x", padx=14)
        scroll = tk.Scrollbar(frame)
        scroll.pack(side="right", fill="y")
        text = tk.Text(frame, wrap="word", bg=BG, fg=FG, font=self.body_font,
                       relief="flat", highlightthickness=0, padx=14, pady=8,
                       spacing1=2, spacing3=2, cursor="arrow",
                       yscrollcommand=scroll.set)
        text.pack(side="left", fill="both", expand=True)
        scroll.config(command=text.yview)
        text.tag_configure("headline", font=self.head_font, spacing1=18,
                           spacing3=6)
        text.tag_configure("number", foreground=MUTED)
        text.tag_configure("hl", background=HIGHLIGHT)
        text.tag_raise("hl")
        for pos, (_, colour) in PARTS_OF_SPEECH.items():
            text.tag_configure(pos, background=colour)
            text.tag_raise(pos)
        # The hovered word and its translation: dark box, light text.
        text.tag_configure("word", background=FG, foreground=BG)
        text.tag_raise("word")
        text.tag_configure("speak", foreground=SPEAK_COLOUR)
        text.tag_bind("speak", "<Button-1>",
                      lambda e, t=text: self.on_speak(t, e))
        text.tag_bind("speak", "<Enter>", lambda e, t=text: t.config(cursor="hand2"))
        text.tag_bind("speak", "<Leave>", lambda e, t=text: t.config(cursor="arrow"))
        text.bind("<Motion>", lambda e, t=text: self.on_motion(t, e))
        text.bind("<Leave>", lambda e: self.on_leave())
        text.config(state="disabled")
        return text

    # -- loading

    def load(self, force=False):
        self.refresh_btn.config(state="disabled")
        self.status.config(
            text="Fetching and summarising today's news with "
                 f"{ai_label(self.settings)} — this takes a few minutes…")
        threading.Thread(target=self._load_worker,
                         args=(dict(self.settings), force),
                         daemon=True).start()

    def _load_worker(self, settings, force):
        try:
            result = load_stories(settings, force), None
        except Exception as exc:  # shown to the user in the status bar
            result = None, str(exc)
        self.root.after(0, self._load_done, *result)

    def _load_done(self, result, error):
        self.refresh_btn.config(state="normal")
        if error:
            self.status.config(text="Could not load the news: " + error)
            return
        stories = result["stories"]
        self.render(stories)
        has_words = any(self.words[text] and any(self.words[text].values())
                        for text in self.panels.values())
        # The colour key only makes sense when the AI supplied word detail.
        if has_words and not self.key.winfo_ismapped():
            self.key.pack(side="bottom", fill="x", padx=24, pady=(0, 10),
                          before=self.panes)
        elif not has_words:
            self.key.pack_forget()
        hints = "hover a sentence to see its translation"
        if has_words:
            hints += ", a word to see its counterpart"
        self.status.config(
            text=f"{FEED_NAME} · {datetime.date.today():%d %B %Y} · "
                 f"{len(stories)} stories by {result.get('ai', '?')} · "
                 f"{hints}; click {SPEAK_GLYPH} to hear the French")

    # -- settings

    def open_settings(self):
        """Dialog for choosing which AI writes the summaries."""
        win = tk.Toplevel(self.root, bg=BG, padx=18, pady=14)
        win.title("Settings")
        win.transient(self.root)
        win.resizable(False, False)
        current = self.settings
        provider = tk.StringVar(value=current["provider"])
        detail = tk.BooleanVar(value=current["word_detail"])
        fields = {}  # settings key -> StringVar

        def heading(text):
            tk.Label(win, text=text, bg=BG, fg=MUTED, font=self.label_font,
                     anchor="w").pack(fill="x", pady=(10, 2))

        def field(parent, label, key, secret=False):
            row = tk.Frame(parent, bg=BG)
            row.pack(fill="x", padx=(24, 0), pady=1)
            tk.Label(row, text=label, bg=BG, fg=FG, width=10,
                     anchor="w").pack(side="left")
            fields[key] = tk.StringVar(value=current[key])
            tk.Entry(row, textvariable=fields[key], width=42,
                     show="\u2022" if secret else "").pack(side="left")

        heading("AI THAT WRITES THE SUMMARIES")
        layout = {
            "claude": [("Model", "claude_model", False)],
            "ollama": [("Address", "ollama_url", False),
                       ("Model", "ollama_model", False)],
            "openai": [("Address", "openai_url", False),
                       ("Model", "openai_model", False),
                       ("API key", "openai_key", True)],
        }
        for name, label in PROVIDERS.items():
            tk.Radiobutton(win, text=label, variable=provider, value=name,
                           bg=BG, fg=FG, activebackground=BG, anchor="w",
                           highlightthickness=0).pack(fill="x")
            for row in layout[name]:
                field(win, *row)

        heading("FEATURES")
        tk.Checkbutton(
            win, variable=detail, bg=BG, fg=FG, activebackground=BG,
            anchor="w", justify="left", highlightthickness=0,
            text="Word detail: part-of-speech colours and word-to-word "
                 "matching.\nTurn off for an AI that is too slow or "
                 "unreliable to produce it.").pack(fill="x")
        tk.Label(win, bg=BG, fg=MUTED, justify="left", anchor="w",
                 text="The API key is stored in settings.json in the app "
                      "folder, readable only by you.\nChanges apply the next "
                      "time the news is fetched.").pack(fill="x", pady=(10, 0))

        def save(refresh):
            self.settings = {
                "provider": provider.get(), "word_detail": detail.get(),
                **{key: var.get().strip() for key, var in fields.items()}}
            save_settings(self.settings)
            win.destroy()
            if refresh:
                self.load(force=True)
            else:
                self.status.config(
                    text="Settings saved. Click Refresh to fetch the news "
                         f"with {ai_label(self.settings)}.")

        buttons = tk.Frame(win, bg=BG)
        buttons.pack(fill="x", pady=(14, 0))
        tk.Button(buttons, text="Save and refresh now",
                  command=lambda: save(True)).pack(side="right")
        tk.Button(buttons, text="Save",
                  command=lambda: save(False)).pack(side="right", padx=6)
        tk.Button(buttons, text="Cancel",
                  command=win.destroy).pack(side="right")

    # -- rendering

    def render(self, stories):
        self.active = None
        self.active_word = None
        for lang, text in self.panels.items():
            text.config(state="normal")
            text.delete("1.0", "end")
            self.words[text] = {}
            sid = 0
            for n, pairs in enumerate(stories, 1):
                for i, pair in enumerate(pairs):
                    tag = f"s{sid}"
                    sid += 1
                    if i == 0:
                        text.insert("end", f"{n}. ", ("headline", "number"))
                    if lang == "fr":
                        self.french[tag] = pair["fr"]
                        style = ("headline",) if i == 0 else ()
                        text.insert("end", SPEAK_GLYPH, style + ("speak", tag))
                        text.insert("end", " ", style + (tag,))
                    start = text.index("end-1c")
                    self.words[text][tag] = [
                        (f"{start}+{a}c", f"{start}+{b}c", pos, link)
                        for a, b, pos, link in locate_words(
                            pair[lang], pair.get(lang + "_pos", []))]
                    if i == 0:
                        text.insert("end", pair[lang], ("headline", tag))
                        text.insert("end", "\n", "headline")
                    else:
                        text.insert("end", pair[lang], (tag,))
                        text.insert("end", " ")
                text.insert("end", "\n")
            text.config(state="disabled")

    # -- hover highlighting

    def sentence_at(self, text, x, y):
        """Return (sentence tag, word number) under pixel (x, y).

        Either may be None: no sentence there, or a gap between words.
        """
        index = text.index(f"@{x},{y}")
        box = text.bbox(index)
        # "@x,y" snaps to the nearest character, so make sure the pointer is
        # really on it and not in the blank space beside or below the text.
        if not box or not (box[0] <= x <= box[0] + box[2]
                           and box[1] <= y <= box[1] + box[3]):
            return None, None
        for tag in text.tag_names(index):
            if re.fullmatch(r"s\d+", tag):
                break
        else:
            return None, None
        for number, (start, end, _, _) in enumerate(self.words[text][tag]):
            if text.compare(start, "<=", index) and text.compare(index, "<", end):
                return tag, number
        return tag, None

    def on_motion(self, text, event):
        tag, number = self.sentence_at(text, event.x, event.y)
        self.set_active(tag, source=text)
        self.set_active_word(text, tag, number)

    def on_speak(self, text, event):
        """Speak the French sentence whose play button was clicked."""
        for tag in text.tag_names(f"@{event.x},{event.y}"):
            if tag in self.french:
                if speech_available():
                    speak_french(self.french[tag])
                else:
                    self.status.config(
                        text="Cannot speak: no Piper voice or spd-say found.")
                return

    def on_leave(self):
        self.set_active(None)
        self.set_active_word(None, None, None)

    def set_active_word(self, source, tag, number):
        """Mark the hovered word and the word(s) that translate it."""
        key = (source, tag, number) if number is not None else None
        if key == self.active_word:
            return
        self.active_word = key
        for text in self.panels.values():
            text.tag_remove("word", "1.0", "end")
        if key is None:
            return
        start, end, _, link = self.words[source][tag][number]
        source.tag_add("word", start, end)
        if not link:
            return  # no counterpart in the other language
        for text in self.panels.values():
            for start, end, _, other in self.words[text].get(tag, ()):
                if other == link:
                    text.tag_add("word", start, end)

    def set_active(self, tag, source=None):
        if tag == self.active:
            return
        self.active = tag
        for text in self.panels.values():
            text.tag_remove("hl", "1.0", "end")
            for pos in PARTS_OF_SPEECH:
                text.tag_remove(pos, "1.0", "end")
            if tag is None:
                continue
            ranges = text.tag_ranges(tag)
            if not ranges:
                continue
            text.tag_add("hl", ranges[0], ranges[1])
            for start, end, pos, _ in self.words[text].get(tag, ()):
                text.tag_add(pos, start, end)
            if text is not source:
                # Keep the counterpart sentence visible in the other panel.
                text.see(ranges[1])
                text.see(ranges[0])


def main():
    root = tk.Tk()
    NewsReader(root)
    root.mainloop()


if __name__ == "__main__":
    main()
