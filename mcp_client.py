import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.environ["NOTION_API_KEY"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

BASE_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# ── MCP-style tools ───────────────────────────────────────────────────────────

def mcp_search_notes(query: str) -> list:
    """MCP tool: search notes by keyword"""
    response = httpx.post(
        f"{BASE_URL}/databases/{NOTION_DATABASE_ID}/query",
        headers=HEADERS,
        json={
            "filter": {
                "or": [
                    {
                        "property": "Summary",
                        "rich_text": {"contains": query}
                    },
                    {
                        "property": "Name",
                        "title": {"contains": query}
                    }
                ]
            },
            "sorts": [{"property": "Date", "direction": "descending"}],
            "page_size": 10
        }
    )
    results = response.json().get("results", [])
    notes = []
    for page in results:
        props = page["properties"]
        title = props["Name"]["title"]
        summary = props["Summary"]["rich_text"]
        date = props["Date"]["date"]
        tags = props["Tags"]["multi_select"]
        notes.append({
            "id": page["id"],
            "title": title[0]["plain_text"] if title else "Untitled",
            "summary": summary[0]["plain_text"] if summary else "",
            "date": date["start"] if date else "unknown",
            "tags": [t["name"] for t in tags]
        })
    return notes

def mcp_create_note(title: str, summary: str, tags: list, date: str) -> dict:
    """MCP tool: create a new note"""
    response = httpx.post(
        f"{BASE_URL}/pages",
        headers=HEADERS,
        json={
            "parent": {"database_id": NOTION_DATABASE_ID},
            "properties": {
                "Name": {"title": [{"text": {"content": title}}]},
                "Date": {"date": {"start": date}},
                "Tags": {"multi_select": [{"name": t} for t in tags]},
                "Summary": {"rich_text": [{"text": {"content": summary}}]}
            }
        }
    )
    return response.json()

def mcp_update_note(page_id: str, summary: str) -> dict:
    """MCP tool: update an existing note"""
    response = httpx.patch(
        f"{BASE_URL}/pages/{page_id}",
        headers=HEADERS,
        json={
            "properties": {
                "Summary": {"rich_text": [{"text": {"content": summary}}]}
            }
        }
    )
    return response.json()

def mcp_list_all_notes(limit: int = 20) -> list:
    """MCP tool: list all notes"""
    response = httpx.post(
        f"{BASE_URL}/databases/{NOTION_DATABASE_ID}/query",
        headers=HEADERS,
        json={
            "sorts": [{"property": "Date", "direction": "descending"}],
            "page_size": limit
        }
    )
    results = response.json().get("results", [])
    notes = []
    for page in results:
        props = page["properties"]
        title = props["Name"]["title"]
        summary = props["Summary"]["rich_text"]
        date = props["Date"]["date"]
        tags = props["Tags"]["multi_select"]
        notes.append({
            "id": page["id"],
            "title": title[0]["plain_text"] if title else "Untitled",
            "summary": summary[0]["plain_text"] if summary else "",
            "date": date["start"] if date else "unknown",
            "tags": [t["name"] for t in tags]
        })
    return notes

# ── MCP tool definitions (for Groq function calling) ─────────────────────────
MCP_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "mcp_search_notes",
            "description": "Search notes in Notion by keyword",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "keyword to search for"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mcp_create_note",
            "description": "Create a new note in Notion",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "date": {"type": "string", "description": "YYYY-MM-DD"}
                },
                "required": ["title", "summary", "tags", "date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mcp_list_all_notes",
            "description": "List all notes from Notion",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

# ── tool dispatcher ───────────────────────────────────────────────────────────
def dispatch_tool(name: str, args: dict):
    if name == "mcp_search_notes":
        return mcp_search_notes(args["query"])
    elif name == "mcp_create_note":
        return mcp_create_note(
            args["title"], args["summary"],
            args["tags"], args["date"]
        )
    elif name == "mcp_list_all_notes":
        return mcp_list_all_notes(20)
    else:
        return {"error": f"Unknown tool: {name}"}
