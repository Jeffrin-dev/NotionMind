import os
import json
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from mcp_client import MCP_TOOLS, dispatch_tool

load_dotenv()

groq = Groq(api_key=os.environ["GROQ_API_KEY"])
console = Console()

SYSTEM_PROMPT = """You are NotionMind Agent — an AI assistant with access to the 
user's Notion workspace via MCP tools.

You have these tools:
- mcp_search_notes: search notes by keyword
- mcp_create_note: create a new note
- mcp_list_all_notes: list all notes (limit must be an integer, default 20)

Rules:
- Always summarise tool results in plain English — never show raw JSON to the user
- For questions about recent work, use mcp_list_all_notes
- For specific topic searches, use mcp_search_notes
- Be concise and friendly

Today's date is: """ + datetime.now().strftime("%Y-%m-%d")

def run_agent(user_message: str):
    """Run the MCP agent with tool calling loop"""
    console.print(f"\n[dim]Agent thinking...[/]")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]

    # agentic loop — keeps running until no more tool calls
    while True:
        response = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=MCP_TOOLS,
            tool_choice="auto",
            max_tokens=1000
        )

        message = response.choices[0].message

        # no tool calls — final answer
        if not message.tool_calls:
           console.print(Panel(
               f"[bold white]{message.content}[/]",
               title="[cyan]NotionMind Agent[/]"
           ))
           
           break

        # process tool calls
        messages.append({
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]
        })

        for tc in message.tool_calls:
            tool_name = tc.function.name
            tool_args = json.loads(tc.function.arguments)

            console.print(f"[dim]→ calling tool: [cyan]{tool_name}[/] with {tool_args}[/]")

            result = dispatch_tool(tool_name, tool_args)

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result)
            })

def interactive_agent():
    console.print(Panel(
        "[bold cyan]NotionMind Agent[/] — MCP-powered Notion AI\n\n"
        "[dim]Ask me anything about your notes.\n"
        "Examples:\n"
        "  'what did I work on this week?'\n"
        "  'create a note about my meeting today'\n"
        "  'show me all notes tagged Python'\n"
        "  'summarise everything I did in March'\n\n"
        "Type 'quit' to exit[/]",
        title="Welcome"
    ))

    while True:
        mode = Prompt.ask("\n[bold cyan]Input mode[/]", choices=["text", "voice"], default="text")
        if mode == "voice":
            from voice import listen
            user_input = listen()
            if not user_input:
                continue
        else:
            user_input = Prompt.ask("[bold cyan]You[/]")
        if user_input.lower() == "quit":
            console.print("[dim]Goodbye![/]")
            break
        run_agent(user_input)

if __name__ == "__main__":
    interactive_agent()
