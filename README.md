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

> **Your Notion workspace, but it thinks back.**

NotionMind is a free, voice-enabled AI agent that uses your Notion workspace as its long-term memory. Save notes by speaking, ask questions about your past work, search by meaning not keywords, trace connections across your knowledge graph, and view a stunning terminal analytics dashboard — all at zero cost.

---

## 🎬 What It Looks Like

```
$ python3 notionmind.py

╭─────────────────────────────────────────────╮
│ NotionMind — Your Notion-powered AI memory  │
│ You have 26 note(s) in your brain.          │
│ 🔊 Voice: online — Jenny neural voice       │
╰─────────────────────────────────────────────╯

> dashboard

◆  N O T I O N M I N D  B R A I N  D A S H B O A R D  ◆
              Monday, 23 March 2026  ·  16:55

╭── 🗓 Brain Activity ──╮     ╭── 📊 Quick Stats ──────╮
│ · · · · █ ▬ ▪ · · ·  │   │ 🗒  Total notes    26   │
│                       │   │ 📅  Today          9   │
╰───────────────────────╯   │ 🔥  Streak      3 days │
                            │ 🏷   Top tag  NotionMind│
                                          ╰────────────────────────╯
```

---

## 🌍 Real World Applications

### 👨‍💻 Developers
- **Daily standup prep** — ask "what did I work on this week?" and get an instant summary
- **Bug log** — save bug fixes as you go, search them months later by meaning
- **Inbox research** — add topics to Notion inbox, run executor, wake up to a full summary

### 📚 Students
- **Study notes** — save lecture notes by speaking, ask questions during revision
- **Exam prep** — ask "summarise everything I learned about machine learning"
- **Todo list** — track assignments by priority and due date

### 💼 Freelancers
- **Work log** — track hours and tasks per client
- **Invoice prep** — search notes by client name to compile billable work

### 🔬 Researchers
- **Automated research** — add topics to inbox, executor searches web and writes summaries
- **Knowledge graph** — AI traces connections across all your notes

### 🏠 Personal Life
- **Fitness tracking** — log workouts by voice, ask for monthly reflections
- **Daily journal** — speak your day, ask for monthly insights

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
| ⚡ **Executor** | Auto-researches tasks via web search, writes results to Notion |
| 📄 **Results** | View completed task results in terminal |
| 🎤 **Voice Input** | Speak instead of type using Google Speech Recognition |
| 🔊 **Voice Output** | Neural TTS — Jenny (Edge TTS) online, espeak offline |
| 🗑️ **Delete** | Remove notes with confirmation |
| 🤖 **MCP Agent** | Natural language → Notion tool calls |
| ⏰ **Scheduler** | Set daily cron jobs to auto-run executor |
| 📅 **Today** | Show only today's notes at a glance |
| 📤 **Export** | Export notes to markdown — filter by date, tag, range, or specific note |
| 📖 **Read** | Read full page content of any note |
| 🌍 **Multi-language** | Voice in English, Hindi, Spanish, French, Tamil, Malayalam |
| 📱 **Telegram Bot** | Control NotionMind from your phone |
| ⏰ **Reminders** | Set reminders with date, time, voice + Telegram notifications |
| 🖼️ **Image Notes** | Save screenshots to Notion — file path or clipboard |
| 📊 **Weekly Report** | Auto-generated weekly summary saved to Notion + Telegram |
| 🤖 **AI Organiser** | Auto-tag, find duplicates, merge notes, auto-categorise |
| 🔄 **Two-way Sync** | Pull, edit locally, push back to Notion with watch mode |
| 📦 **Knowledge Base** | Save code snippets, terminal commands, bookmarks |
| 🧠 **Knowledge Graph** | AI-powered note connections — view, relate, find paths |
| 🔍 **Semantic Search** | Search by meaning using fastembed — finds "Kerala cricketer" even if keywords differ |
| 💡 **Think** | Multi-hop reasoning — traces connections across notes + graph |
| 📈 **Recall** | How your understanding of a topic evolved over time |
| 💬 **Suggest** | Auto-suggests related notes every time you save |
| 📊 **Dashboard** | Terminal analytics — heatmap, growth chart, topic velocity, reminders, todos |
| 🔮 **Insights** | AI-powered personal insights — peak productivity, knowledge gaps, fading topics |
| ✅ **Todo List** | Priority todos stored in Notion — due dates, complete, delete |

---

## 🆓 Free Stack

| Component | Tool | Cost |
|---|---|---|
| AI Brain | Groq — Llama 3.3 70B + Llama 3.1 8B | Free tier |
| Workspace | Notion API | Free |
| Semantic Search | fastembed (BAAI/bge-small-en-v1.5) | Free — runs locally |
| Web Search | DuckDuckGo (ddgs) | Free |
| Voice Input | Google Speech Recognition | Free |
| Voice Output (online) | Microsoft Edge TTS — Jenny Neural | Free |
| Voice Output (offline) | espeak + MBROLA | Free |
| Telegram Bot | python-telegram-bot | Free |
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
            pyaudio edge-tts pygame schedule \
            python-telegram-bot Pillow fastembed numpy
```

### 4. Install system dependencies (Linux)
```bash
sudo apt install portaudio19-dev espeak mbrola mbrola-en1 mpg123 xclip -y
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
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
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

# Reminder daemon
python3 reminders.py

# Telegram Bot
python3 telegram_bot.py
```

---

## 💡 The Killer Daily Workflow

```bash
# Morning — check what's on
python3 notionmind.py
> dashboard          # heatmap, growth, todos, reminders at a glance
> insights           # AI surfaces what matters today

# During the day — save notes instantly
python3 notionmind.py save "Fixed the auth bug — JWT expiry was miscalculated"

# Search by meaning, not just keywords
> graph → search
What are you looking for: authentication bug fixes

# Add research tasks
python3 notionmind.py inbox "Research best Python libraries for data viz in 2026"

# Evening — let the agent do the research
python3 executor.py
```

---

## 📁 Project Structure

```
notionmind/
├── notionmind.py    # Main CLI
├── agent.py         # MCP-powered natural language agent
├── executor.py      # Autonomous task executor with web search + weekly report
├── mcp_client.py    # Notion MCP tool definitions and dispatcher
├── search.py        # Free DuckDuckGo web search
├── voice.py         # Voice input/output + multi-language
├── scheduler.py     # Cron + Python scheduler
├── organiser.py     # AI auto-organiser
├── sync.py          # Two-way sync
├── knowledge.py     # Knowledge base
├── brain.py         # Knowledge graph + semantic search + think + recall
├── analytics.py     # Terminal dashboard + AI insights
├── todos.py         # Todo list stored in Notion
├── reminders.py     # Reminders with voice + Telegram
├── image.py         # Image notes via Notion File Upload API
├── telegram_bot.py  # Telegram bot
├── .env.example     # API key template
├── .gitignore
├── README.md
├── LICENSE          # MIT
├── CONTRIBUTING.md
└── CHANGELOG.md
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
