# Changelog

All notable changes to NotionMind will be documented here.

Format: [Semantic Versioning](https://semver.org)

---

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

### [1.1.0] — Planned
- ⏰ **Scheduled executor** — runs automatically at set times via cron
- 🌍 **Multi-language voice** — Hindi, Spanish, French support
- 📤 **Export notes** — save all notes as a markdown file
- 📅 **`today` command** — show only today's notes at a glance
- 📖 **Notion page reading** — read full page content, not just database rows
- 📱 **Telegram bot** — control NotionMind from your phone

### [1.2.0] — Future
- 🖼️ **Image notes** — save screenshots to Notion via CLI
- 📊 **Weekly report** — auto-generated weekly summary every Sunday
- 🔔 **Reminders** — set reminders that notify via voice
