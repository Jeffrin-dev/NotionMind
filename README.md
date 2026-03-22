# NotionMind 🧠

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-1.0.0-brightgreen)
![Notion MCP](https://img.shields.io/badge/Notion-MCP%20Powered-black?logo=notion)
![Voice](https://img.shields.io/badge/Voice-Edge%20TTS%20%7C%20espeak-purple)
![Cost](https://img.shields.io/badge/Cost-%240%2Fmonth-success)
![Groq](https://img.shields.io/badge/Groq-Llama%203.3%2070B-orange?logo=groq)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20WSL2-lightgrey)
![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen)

> **Your Notion workspace, but it talks back.**

NotionMind is a free, voice-enabled AI agent that uses your Notion workspace as its long-term memory. Save notes by speaking, ask questions about your past work, and let the agent automatically research topics and write results back to Notion — all at zero cost.

---

## 🎬 What It Looks Like

```
$ python3 notionmind.py

╭─────────────────────────────────────────────╮
│ NotionMind — Your Notion-powered AI memory  │
│ You have 15 note(s) in your brain.          │
│ 🔊 Voice: online — Jenny neural voice       │
│                                             │
│ Commands:                                   │
│   save    — save a new note                 │
│   ask     — ask a question about your notes │
│   inbox   — add a research task             │
│   voice   — speak instead of type           │
│   ...and more                               │
╰─────────────────────────────────────────────╯

> ask
What do you want to know: what did I work on this week?

Searching your Notion notes...
╭─────────────────── NotionMind Answer ───────────────────╮
│ This week you built NotionMind — an MCP-powered AI      │
│ agent with voice input/output, task execution, web      │
│ search, and Notion as persistent memory.                │
╰─────────────────────────────────────────────────────────╯
🔊 Speaking answer...
```

---

## 🌍 Real World Applications

### 👨‍💻 Developers
- **Daily standup prep** — ask "what did I work on this week?" and get an instant summary from your own notes
- **Bug log** — save bug fixes as you go, search them months later by keyword
- **Inbox research** — add "research X topic" to Notion inbox, run executor, wake up to a full summary

### 📚 Students
- **Study notes** — save lecture notes by speaking, ask questions during revision
- **Exam prep** — ask "summarise everything I learned about machine learning" and get a digest from your own notes

### 💼 Freelancers
- **Work log** — track hours and tasks per client, ask "how much did I work for X this month?"
- **Invoice prep** — search notes by client name to compile billable work

### 🔬 Researchers
- **Automated research** — add topics to Notion inbox, executor searches web and writes summaries back overnight
- **Knowledge base** — everything saved, searchable, queryable in plain English

### 🏠 Personal Life
- **Fitness tracking** — log workouts by voice, ask "how consistent was I this month?"
- **Daily journal** — speak your day, ask for monthly reflections

---

## ✨ Features

| Feature | Description |
|---|---|
| 💾 **Smart Save** | AI auto-generates title, tags, and date from plain text |
| 🧠 **Ask** | AI searches your Notion notes and answers questions |
| 📋 **List** | View all notes in a clean table |
| 🔍 **Search** | Filter notes by keyword |
| 📊 **Stats** | Streak counter, note count, top tags |
| 📥 **Inbox** | Add research tasks from CLI |
| ⚡ **Executor** | Auto-researches tasks via web search, writes results to Notion, marks Done |
| 📄 **Results** | View completed task results in terminal |
| 🎤 **Voice Input** | Speak instead of type using Google Speech Recognition |
| 🔊 **Voice Output** | Neural TTS — Jenny (Edge TTS) online, espeak offline |
| 🗑️ **Delete** | Remove notes with confirmation |
| 🤖 **MCP Agent** | Natural language → Notion tool calls |
| ⏰ **Scheduler** | Set daily cron jobs to auto-run executor even when terminal is closed |
| 📅 **Today** | Show only today's notes at a glance |
| 📤 **Export** | Export notes to markdown — filter by date, tag, range, or pick a specific note |

---

## 🆓 Free Stack

| Component | Tool | Cost |
|---|---|---|
| AI Brain | Groq — Llama 3.3 70B | Free tier |
| Workspace | Notion API | Free |
| Web Search | DuckDuckGo (ddgs) | Free |
| Voice Input | Google Speech Recognition | Free |
| Voice Output (online) | Microsoft Edge TTS — Jenny Neural | Free |
| Voice Output (offline) | espeak + MBROLA | Free |
| Language | Python 3.10+ | Free |

**Total monthly cost: $0**

---

## 🚀 Setup

### Prerequisites
- Python 3.10+
- A free Notion account
- A free Groq account

### 1. Clone the repo
```bash
git clone https://github.com/Jeffrin-dev/NotionMind.git
cd NotionMind
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows (WSL2)
```

### 3. Install Python dependencies
```bash
pip install notion-client==2.2.1 groq python-dotenv rich \
            httpx mcp httpx-sse ddgs SpeechRecognition \
            pyaudio edge-tts pygame
```

### 4. Install system dependencies (Linux)
```bash
sudo apt install portaudio19-dev espeak mbrola mbrola-en1 mpg123 -y
```

### 5. Set up API keys

**Notion API key:**
- Go to notion.so/my-integrations → New integration → copy the secret

**Notion Database ID:**
- Create a Notion database with columns: `Name`, `Date`, `Tags`, `Summary`
- Connect your integration to it
- Copy the ID from the URL

**Groq API key:**
- Go to console.groq.com → API Keys → Create (free)

```bash
cp .env.example .env
```

Edit `.env`:
```
NOTION_API_KEY=secret_your_key_here
NOTION_DATABASE_ID=your_database_id_here
GROQ_API_KEY=gsk_your_key_here
```

### 6. Run

```bash
# Interactive CLI — daily notes + questions
python3 notionmind.py

# MCP Agent — natural language Notion queries
python3 agent.py

# Task Executor — processes inbox, searches web, writes to Notion
python3 executor.py

# Scheduler (cron + manual trigger)
python3 scheduler.py

# Check execution log
cat executor.log
```

---

## 💡 The Killer Daily Workflow

```bash
# Morning — check what's pending
python3 agent.py
> what's pending in my inbox?
> what did I work on yesterday?

# During the day — save notes instantly
python3 notionmind.py save "Fixed the auth bug — JWT expiry was miscalculated"

# Add research tasks
python3 notionmind.py inbox "Research best Python libraries for data viz in 2026"

# Evening — let the agent do the research while you rest
python3 executor.py
# → searches web for each inbox task
# → writes results back to Notion
# → marks tasks as Done
# → creates daily summary page
```

---

## 📁 Project Structure

```
notionmind/
├── notionmind.py    # Main CLI — save, ask, list, search, stats, voice, delete
├── agent.py         # MCP-powered natural language agent
├── executor.py      # Autonomous task executor with web search
├── mcp_client.py    # Notion MCP tool definitions and dispatcher
├── search.py        # Free DuckDuckGo web search
├── voice.py         # Voice input (Google STT) + output (Edge TTS / espeak)
├── .env.example     # API key template
├── scheduler.py     # Scheduled executor with cron support
├── README.md
└── executor.log     # Auto-generated execution log (not tracked in git)
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md)

## 📄 License

MIT — see [LICENSE](LICENSE)

---

Built for the [Notion MCP Challenge](https://dev.to) · March 2026 · by [@Jeffrin-dev](https://github.com/Jeffrin-dev)
