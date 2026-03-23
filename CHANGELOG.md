# Changelog

All notable changes to NotionMind will be documented here.

Format: [Semantic Versioning](https://semver.org)

---

## [1.3.0] — 2026-03-23
 
### ✨ New Features
 
#### Knowledge Graph — Part 3
#### Todo List (`todos.py`, `notionmind.py`, `analytics.py`)
- New `todos.py` — full todo list stored in Notion database
- Add todos with priority (high/medium/low), due date, and optional note
- Priority stored as `priority-high/medium/low` tags in Notion
- List pending todos — sorted by priority then due date
- Mark complete — moves from `todo` tag to `todo-done` tag
- Delete todos with confirmation
- View completed todos
- Overdue todos highlighted in red, today's todos in yellow
- `todo` command in interactive mode and CLI
- Todos panel in dashboard — shows up to 6 pending todos with priority icons
 
#### Analytics Dashboard (`analytics.py`, `notionmind.py`)
- New `analytics.py` — stunning terminal analytics dashboard
- `dashboard` command — full two-row panel layout:
  - Row 1: GitHub-style 30-day activity heatmap + quick stats panel
  - Row 2: 14-day knowledge growth bar chart + topic velocity with trend arrows
  - Row 3: Upcoming reminders panel + pending todos panel (side by side)
- Activity heatmap uses heat characters (· ▪ ▫ ▬ █) colored grey → bright green
- Topic velocity shows each tag's count this week vs last week with ↑ ↓ → trend arrows
- Overdue reminders and todos highlighted in yellow/red
- `insights` command — AI-powered personal insights using Groq llama-3.3-70b:
  - 🔥 Peak Productivity — when you're most active, specific dates cited
  - 🕳 Knowledge Gaps — topics being underexplored given current work
  - 📉 Fading Topics — what you explored before but drifted from
  - ⚡ This Week's Action — one sharp actionable recommendation
  - Each section rendered as a distinct colored Rich panel
 



#### Knowledge Graph — Part 2
#### Semantic Search (`brain.py`)
- New `semantic_search()` — vector similarity search using fastembed locally
- Model: BAAI/bge-small-en-v1.5 (~67MB, cached at ~/.cache/fastembed)
- Runs entirely on CPU — no API, no cost, no internet required after first download
- Fetches full Notion page block content for each note — not just summary
- Notes cache (`_notes_cache`, `_get_notes()`) — fetches all notes + full content once per session, reused across all searches
- Filters out auto-generated, summary, daily, weekly-report, category, merged notes
- Threshold: 0.55 cosine similarity minimum to surface a result
- Attribute-aware: "cricketer from Kerala" correctly finds the Kerala cricketer note
- `7. Search` in graph menu — interactive semantic search with scored results table
 
#### Think — Multi-hop Reasoning (`brain.py`)
- New `think()` function — complex question answering across notes + graph
- Extracts keywords from question using Groq, searches each separately
- Merges results from multiple keyword searches using notes cache
- Expands one hop via knowledge graph edges to pull in connected notes
- Builds structured context: directly relevant notes + connected notes + known connections
- Strict system prompt — never invents note titles, only cites exact titles from context
- `8. Think` in graph menu
 
#### Recall — Knowledge Evolution (`brain.py`)
- New `recall()` function — chronological topic understanding analysis
- Finds all notes semantically related to a topic, sorted by date
- Groq narrates the arc: initial curiosity → experiments → insights → current depth
- Suggests natural next questions if only one note found
- Ends with one sentence on where the topic seems headed
- `9. Recall` in graph menu
 
#### Suggest — Auto Related Notes (`brain.py`, `notionmind.py`)
- `suggest_related()` now uses fastembed semantic search instead of Groq
- Invalidates notes cache after each save so new note is excluded from its own suggestions
- Filters out auto-generated, summary, daily notes from suggestions
- Shows up to 3 related notes after every save, automatically
 
---

#### Knowledge Graph — Part 1 (`brain.py`, `notionmind.py`)
- New `brain.py` — AI-powered knowledge graph engine
- `build` — analyses all notes, finds genuine content connections using Groq
- `view` — ASCII tree visualisation with strength bars
- `relate` — manually link two notes with custom reason and strength
- `neighbours` — show all connections of a specific note
- `path` — BFS shortest path between any two notes
- `strongest` — top 15 connections ranked by strength
- Incremental builds — only checks new pairs, not full rebuild
- Strict semantic matching — ignores temporal/project-based false connections
- Graph stored locally at `~/.notionmind_graph.json`
- `graph` command in interactive mode and CLI

#### Knowledge Base (`knowledge.py`, `notionmind.py`)
- New `knowledge.py` — code snippets, commands, bookmarks
- Save code snippets with language and syntax highlighting
- Save terminal commands with description and example usage
- Save bookmarks with URL and auto-fetched page title
- Browse KB — filter by all, snippets, commands, bookmarks
- Search across entire knowledge base
- View full content with Rich syntax highlighting (monokai theme)
- All KB items stored in Notion tagged `kb`
- `kb` command in interactive mode and CLI

#### Two-way Sync (`sync.py`, `notionmind.py`)
- New `sync.py` — two-way sync between local cache and Notion
- `pull` — fetches all notes from Notion to local cache (`~/.notionmind_cache.json`)
- `push` — pushes local edits back to Notion
- `edit` — open any note in terminal editor (nano/vim), auto-marks as edited
- `watch` — polls Notion every 30 seconds, shows new/updated/deleted notes in real time
- Cache stored at `~/.notionmind_cache.json` (excluded from git)
- `sync` command in interactive mode and CLI

#### AI Auto-Organiser (`organiser.py`, `notionmind.py`)
- New `organiser.py` — standalone AI organiser
- Auto-tag untagged notes using Groq
- Find duplicate notes using AI similarity detection
- Select duplicate pairs by number and merge them
- Merged content generated by Groq — removes repetition, keeps unique info
- Original notes archived after merge
- Auto-categorise all notes into 3-6 meaningful categories
- Category summaries saved to Notion tagged `category`, `auto-generated`
- Run all — full organise in one command
- `organise` command in interactive mode and CLI


## [1.2.0] — 2026-03-23

### ✨ New Features

#### Weekly Report (`executor.py`, `notionmind.py`, `scheduler.py`)
- New `generate_weekly_report()` in `executor.py`
- Summarises week's notes into 5 sections using Groq
- Sections: Key Achievements, Work Done, Things Learned, Pending Tasks, Focus for Next Week
- Saves report to Notion tagged `weekly-report`, `auto-generated`
- Sends report to Telegram automatically
- `weekly` command in interactive mode and CLI
- `weekly` option in `scheduler.py` — set cron to run every Sunday

#### Image Notes (`image.py`, `notionmind.py`)
- New `image.py` — handles image upload to Notion
- Save screenshots or images directly to Notion via CLI
- Supports file path or clipboard as image source
- Images stored privately in Notion workspace (not third party)
- Supports PNG, JPG, JPEG, GIF, WEBP formats
- 3-step Notion File Upload API: create → send → attach
- `image` command in interactive mode and CLI

#### Reminders (`reminders.py`, `notionmind.py`)
- New `reminders.py` — standalone reminder daemon
- Set one-time or daily repeating reminders
- Voice notification when reminder triggers (Edge TTS / espeak)
- Telegram notification via direct API — no bot process needed
- `remind` command — set a new reminder interactively
- `reminders` command — list all pending reminders
- Delete reminders with confirmation
- CLI: `python3 notionmind.py remind "message" at 18:30`
- Run daemon: `python3 reminders.py`
- Reminders stored locally in `reminders.json`
- Reminders now support specific date and time (YYYY-MM-DD HH:MM)
- Press Enter to default to today's date
- Daily reminders auto-advance to next date after triggering
- Backwards compatible with old reminders without date field

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

