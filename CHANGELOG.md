# Changelog

All notable changes to NotionMind will be documented here.

Format: [Semantic Versioning](https://semver.org)

---

## [1.1.0] — 2026-03-22

### ✨ New Features

#### Telegram Bot (`telegram_bot.py`)
- Control NotionMind from your phone via Telegram
- `/save` — save a note to Notion
- `/ask` — ask questions from your notes
- `/today` — show today's notes
- `/list` — show recent 10 notes
- `/search` — filter notes by keyword
- `/stats` — streak, count, top tags
- `/inbox` — add research task
- `/export` — export all notes as markdown file

#### Multi-language Voice Support (`voice.py`, `notionmind.py`)
- 6 languages supported: English, Hindi, Spanish, French, Tamil, Malayalam
- New `select_language()` function — pick language interactively
- Edge TTS neural voices per language (online)
- espeak fallback per language (offline)
- Google STT language code auto-switches with selected language
- New `lang` command in interactive menu
- Welcome screen shows current language

#### Notion Page Content Reading (`notionmind.py`, `mcp_client.py`)
- New `read_page()` function — pick a note and read its full content
- New `mcp_read_page()` in `mcp_client.py` — fetches Notion blocks API
- Supports headings, paragraphs, bullet points, numbered lists, code blocks, quotes, dividers, to-do items
- Falls back to Summary property when no blocks found
- Available in interactive mode and as CLI argument (`python3 notionmind.py read`)

#### `today` Command (`notionmind.py`)
- New `show_today()` function — filters and displays only today's notes
- Shows title, tags, and summary in a clean rich table
- Available in interactive mode and as CLI argument (`python3 notionmind.py today`)
- Friendly message if no notes exist for today

#### Scheduled Executor (`scheduler.py`)
- `cron` — sets a daily cron job, runs even when terminal is closed
- `python` — Python-based scheduler, runs while terminal is open
- `run` — manually trigger executor from scheduler menu
- `remove` — remove existing cron job
- Auto-detects venv Python path for correct execution
- Logs output to `executor.log` via cron

#### Export to Markdown (`notionmind.py`)
- New `export_notes()` function — exports notes to a `.md` file
- Filter options: all notes, today only, by tag, by date range, or a specific note
- Filename auto-generated based on filter (e.g. `notionmind_export_tag_done.md`)
- Available in interactive mode and as CLI argument (`python3 notionmind.py export`)


## [1.0.0] — 2026-03-21

### 🎉 Initial Release

#### Core CLI (`notionmind.py`)
- `save` — AI auto-generates title, tags and date from plain text, saves to Notion
- `ask` — AI searches Notion notes and answers questions in natural language
- `list` — displays all notes in a rich formatted table
- `search` — filters notes by keyword across title and summary
- `stats` — shows total note count, streak counter, and top tags
- `inbox` — adds research tasks tagged `inbox` for the executor
- `results` — displays completed task results in terminal
- `delete` — removes notes with numbered list and confirmation
- `voice` — full voice mode: speak input, hear output
- Welcome screen shows live note count and voice status

#### MCP Agent (`agent.py`)
- Natural language interface to Notion workspace
- Tool calling loop with `mcp_search_notes`, `mcp_create_note`, `mcp_list_all_notes`
- Powered by Groq Llama 3.3 70B (free tier)
- Answers in plain English — no raw JSON shown to user

#### Task Executor (`executor.py`)
- Reads all notes tagged `inbox` from Notion automatically
- Searches the web via DuckDuckGo for each task
- Writes full research results back to Notion
- Auto-changes tag from `inbox` → `done`
- Creates a daily summary note in Notion

#### Notion MCP Client (`mcp_client.py`)
- MCP-style tool definitions for Groq function calling
- `mcp_search_notes` — keyword search across Notion database
- `mcp_create_note` — create new notes with all properties
- `mcp_update_note` — update existing note summaries
- `mcp_list_all_notes` — retrieve recent notes sorted by date

#### Web Search (`search.py`)
- Free DuckDuckGo search via `ddgs`
- Returns title, snippet, and source URL
- No API key required

#### Voice (`voice.py`)
- **Input:** Google Speech Recognition via microphone
- **Output (online):** Microsoft Edge TTS — Jenny Neural voice
- **Output (offline):** espeak + MBROLA fallback
- Auto-detects internet connection and switches engine
- Confirm before saving misheard speech
- Cleans markdown symbols before speaking

---

## Upcoming

### [1.2.0] — Future
- 🖼️ **Image notes** — save screenshots to Notion via CLI
- 📊 **Weekly report** — auto-generated weekly summary every Sunday
- 🔔 **Reminders** — set reminders that notify via voice
