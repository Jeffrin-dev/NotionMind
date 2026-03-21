# Contributing to NotionMind 🧠

Thank you for your interest in contributing! NotionMind is a free,
open-source project and welcomes contributions of all kinds.

---

## 🐛 Reporting Bugs

1. Check [existing issues](https://github.com/Jeffrin-dev/NotionMind/issues) first
2. Open a new issue with:
   - What you did
   - What you expected
   - What actually happened
   - Your OS and Python version

---

## 💡 Suggesting Features

Open an issue with the `enhancement` label. Describe:
- The problem it solves
- How you'd want it to work
- Any real-world use case

---

## 🛠️ Contributing Code

### Setup
```bash
git clone https://github.com/Jeffrin-dev/NotionMind.git
cd NotionMind
python3 -m venv venv
source venv/bin/activate
pip install notion-client==2.2.1 groq python-dotenv rich \
            httpx mcp httpx-sse ddgs SpeechRecognition \
            pyaudio edge-tts pygame
cp .env.example .env
# fill in your API keys
```

### Workflow
1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Test manually with `python3 notionmind.py`
5. Commit: `git commit -m "feat: describe your change"`
6. Push: `git push origin feature/your-feature-name`
7. Open a Pull Request

### Commit Message Format
```
feat: add new feature
fix: fix a bug
docs: update documentation
refactor: restructure code without changing behavior
```

---

## 📁 Codebase Overview

| File | Purpose |
|---|---|
| `notionmind.py` | Main CLI interface |
| `agent.py` | MCP-powered natural language agent |
| `executor.py` | Autonomous task executor |
| `mcp_client.py` | Notion MCP tools and dispatcher |
| `search.py` | DuckDuckGo web search |
| `voice.py` | Voice input/output |

---

## ✅ Good First Issues

- Add support for more voice languages
- Add a `--quiet` flag to suppress voice output
- Add note export to markdown file
- Add support for Notion databases with custom column names
- Add a `today` command that shows only today's notes

---

## 📄 License

By contributing, you agree your contributions will be licensed under the MIT License.
