# NotionMind 🧠

A free, voice-enabled AI agent that uses Notion as its brain.
Save notes, ask questions, execute research tasks — all powered by
Notion MCP, Groq, and local voice recognition.

## Features
- `save`    — AI auto-titles, tags and saves notes to Notion
- `ask`     — AI searches Notion and answers in text + voice
- `list`    — view all notes in a table
- `search`  — filter notes by keyword
- `stats`   — streak, note count, top tags
- `inbox`   — add research tasks for the agent
- `results` — view completed task results
- `voice`   — speak instead of type (input + output)
- `delete`  — remove a note
- `executor`— reads inbox tasks, searches web, writes results back to Notion

## Voice
- 🔊 Online: Microsoft Edge TTS (Jenny Neural — ChatGPT quality)
- 🔊 Offline: espeak + MBROLA fallback

## Free Stack
- Notion API (free)
- Groq free tier — Llama 3.3 70B
- DuckDuckGo search (free, no API key)
- Edge TTS (free, neural voice)
- Python 3.10+
- Zero cost forever

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/notionmind
cd notionmind
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install notion-client==2.2.1 groq python-dotenv rich \
            httpx mcp httpx-sse ddgs SpeechRecognition \
            pyaudio edge-tts pygame
```

### 4. System dependencies
```bash
sudo apt install portaudio19-dev espeak mbrola mbrola-en1 mpg123 -y
```

### 5. Create .env file
```bash
cp .env.example .env
```
Fill in your keys:
```
NOTION_API_KEY=secret_xxx
NOTION_DATABASE_ID=xxx
GROQ_API_KEY=gsk_xxx
```

### 6. Run
```bash
# Interactive CLI
python3 notionmind.py

# MCP Agent
python3 agent.py

# Task Executor
python3 executor.py
```

## Get your free API keys
- Notion API: notion.so/my-integrations
- Groq API: console.groq.com (free tier)

## Built for
Notion MCP Challenge on dev.to — March 2026

## License
MIT
