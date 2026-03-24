# Changelog

All notable changes to NotionMind will be documented here.

Format: [Semantic Versioning](https://semver.org)

---

## [1.3.0] — 2026-03-24

### ✨ New Features

#### Natural Language Command Routing (`notionmind.py`)
- Type anything in plain English — Groq routes it to the right command automatically
- "who is Sachin Tendulkar" → routes to `ask`
- "i studied for JEE maths today" → routes to `save`
- "show me my notes" → routes to `list`
- Exact command names bypass Groq entirely — zero latency for power users
- Unknown inputs handled gracefully with a helpful message
- `show_help()` — clean grouped command panel replacing the messy choices list

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
- `dashboard` command — full panel layout:
  - Row 1: GitHub-style 30-day activity heatmap + quick stats panel
  - Row 2: 14-day knowledge growth bar chart + topic velocity with trend arrows
  - Row 3: Upcoming reminders panel + pending todos panel (side by side)
- Activity heatmap uses heat characters (· ▪ ▫ ▬ █) colored grey → bright green
- Topic velocity shows each tag's count this week vs last week with ↑ ↓ → trend arrows
- `insights` command — AI-powered personal insights using Groq llama-3.3-70b:
  - 🔥 Peak Productivity — when you're most active, specific dates cited
  - 🕳 Knowledge Gaps — topics being underexplored given current work
  - 📉 Fading Topics — what you explored before but drifted from
  - ⚡ This Week's Action — one sharp actionable recommendation
  - Each section rendered as a distinct colored Rich panel

#### Semantic Search (`brain.py`)
- Vector similarity search using fastembed locally
- Model: BAAI/bge-small-en-v1.5 (~67MB, cached at ~/.cache/fastembed)
- Runs entirely on CPU — no API, no cost, no internet after first download
- Fetches full Notion page block content — not just summary
- Notes cache — fetches all notes + full content once per session
- Filters out auto-generated, summary, daily, weekly-report, category, merged notes
- Threshold: 0.55 cosine similarity minimum
- Attribute-aware: "cricketer from Kerala" correctly finds the Kerala cricketer note
- `7. Search` in graph menu

#### Think — Multi-hop Reasoning (`brain.py`)
- Complex question answering across notes + graph
- Extracts keywords using Groq, searches each separately
- Expands one hop via knowledge graph edges
- Strict prompt — never invents note titles
- `8. Think` in graph menu

#### Recall — Knowledge Evolution (`brain.py`)
- Chronological topic understanding analysis
- Finds all notes semantically related to a topic, sorted by date
- Groq narrates: initial curiosity → experiments → insights → current depth
- `9. Recall` in graph menu

#### Suggest — Auto Related Notes (`brain.py`, `notionmind.py`)
- Groq extracts the single main keyword from a saved note
- Ignores noise words like "today", "watched", "done"
- Searches title + summary only — fast, no full page fetch
- Keyword split matching — "jee maths" matches notes with "jee" or "maths"
- Shows up to 3 related notes after every save

#### Full-featured Telegram Bot (`telegram_bot.py`)
- All commands available on Telegram:
- `/save`, `/ask`, `/today`, `/list`, `/search`, `/semantic`, `/read`, `/delete`
- `/stats`, `/export`, `/inbox`, `/results`, `/weekly`
- `/todos`, `/addtodo`, `/donetodo`
- `/remind`, `/reminders`
- `/think`, `/recall`, `/dashboard`, `/insights`
- `/menu` — shows all available commands in a grouped list

---

## [1.2.0] — 2026-03-23

### ✨ New Features

#### Knowledge Graph (`brain.py`, `notionmind.py`)
- AI-powered note connections engine
- `build` — analyses all notes, finds genuine content connections using Groq
- `view` — ASCII tree visualisation with strength bars
- `relate` — manually link two notes
- `neighbours` — show all connections of a note
- `path` — BFS shortest path between two notes
- `strongest` — top 15 connections ranked by strength
- Incremental builds — skips already-checked pairs
- Graph stored at `~/.notionmind_graph.json`

#### Knowledge Base (`knowledge.py`)
- Save code snippets with language + syntax highlighting
- Save terminal commands with description and example
- Save bookmarks with URL and auto-fetched page title
- Browse KB — filter by type, search across all items

#### Two-way Sync (`sync.py`)
- `pull` — fetch latest from Notion to local cache
- `push` — push local edits back to Notion
- `edit` — open any note in terminal editor
- `watch` — real-time polling for changes

#### AI Auto-Organiser (`organiser.py`)
- Auto-tag untagged notes using Groq
- Find duplicate notes using AI similarity detection
- Merge duplicate pairs — removes repetition, keeps unique info
- Auto-categorise all notes into 3-6 meaningful categories

#### Weekly Report (`executor.py`)
- Summarises week's notes into 5 sections using Groq
- Saves to Notion + sends to Telegram automatically

#### Image Notes (`image.py`)
- Save screenshots to Notion via file path or clipboard
- 3-step Notion File Upload API: create → send → attach

#### Reminders (`reminders.py`)
- Date + time + repeat (once/daily)
- Voice notification + Telegram notification
- Stored in `reminders.json`

---

## [1.1.0] — 2026-03-22

### ✨ New Features

#### Telegram Bot (`telegram_bot.py`)
- `/save`, `/ask`, `/today`, `/list`, `/search`, `/stats`, `/inbox`, `/export`

#### Multi-language Voice (`voice.py`)
- English, Hindi, Spanish, French, Tamil, Malayalam
- Edge TTS neural voices + espeak fallback per language

#### Notion Page Content Reading
- `read_page()` — full Notion block content
- Supports headings, paragraphs, bullets, code blocks, quotes, to-dos

#### Today Command
- Filters and displays only today's notes

#### Scheduled Executor (`scheduler.py`)
- `cron` — daily cron job
- `python` — Python scheduler
- `weekly` — every Sunday for weekly report

#### Export to Markdown
- Filter by all, today, tag, date range, or specific note

---

## [1.0.0] — 2026-03-21

### 🎉 Initial Release

#### Core CLI (`notionmind.py`)
- `save` — AI auto-generates title, tags, date — saves to Notion
- `ask` — AI searches notes and answers in natural language (date-aware)
- `list`, `search`, `stats`, `delete`
- `inbox` — adds research tasks tagged `inbox`
- `results` — displays completed tasks
- `voice` — full voice mode: speak input, hear output

#### MCP Agent (`agent.py`)
- Natural language interface powered by Groq Llama 3.3 70B
- Tool calling loop — `mcp_search_notes`, `mcp_create_note`, `mcp_list_all_notes`

#### Task Executor (`executor.py`)
- Reads `inbox` notes, searches web via DuckDuckGo
- Writes research results back to Notion
- Auto-tags `inbox` → `done`
- Creates daily summary note

#### Notion MCP Client (`mcp_client.py`)
- Full CRUD for Notion database
- 30s timeout on all API calls

#### Web Search (`search.py`)
- Free DuckDuckGo — no API key required

#### Voice (`voice.py`)
- Input: Google Speech Recognition
- Output: Edge TTS (online) + espeak (offline)

---
