import os
import httpx
import subprocess
from rich.console import Console

console = Console()

NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28"
}

# ── step 1: create file upload object ────────────────────────────────────────
def create_file_upload(filename: str, content_type: str) -> str:
    response = httpx.post(
        "https://api.notion.com/v1/file_uploads",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"filename": filename, "content_type": content_type}
    )
    data = response.json()
    if "id" not in data:
        raise Exception(f"Create upload failed: {data}")
    return data["id"]

# ── step 2: send file content ─────────────────────────────────────────────────
def send_file(file_upload_id: str, filepath: str, content_type: str):
    with open(filepath, "rb") as f:
        response = httpx.post(
            f"https://api.notion.com/v1/file_uploads/{file_upload_id}/send",
            headers=HEADERS,
            files={"file": (os.path.basename(filepath), f, content_type)},
            timeout=30
        )
    data = response.json()
    if data.get("status") != "uploaded":
        raise Exception(f"Send file failed: {data}")

# ── step 3: attach to notion page ────────────────────────────────────────────
def attach_image_to_page(page_id: str, file_upload_id: str, caption: str):
    response = httpx.patch(
        f"https://api.notion.com/v1/blocks/{page_id}/children",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={
            "children": [
                {
                    "type": "image",
                    "image": {
                        "type": "file_upload",
                        "file_upload": {"id": file_upload_id},
                        "caption": [{"type": "text", "text": {"content": caption}}]
                    }
                }
            ]
        }
    )
    return response.json()

# ── main upload function ──────────────────────────────────────────────────────
def upload_image_to_notion(filepath: str, caption: str, page_id: str):
    from dotenv import load_dotenv
    load_dotenv()

    # detect content type
    ext = os.path.splitext(filepath)[1].lower()
    content_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp"
    }
    content_type = content_types.get(ext, "image/png")
    filename = os.path.basename(filepath)

    console.print("[dim]Creating upload object...[/]")
    file_upload_id = create_file_upload(filename, content_type)

    console.print("[dim]Uploading image to Notion...[/]")
    send_file(file_upload_id, filepath, content_type)

    console.print("[dim]Attaching to page...[/]")
    attach_image_to_page(page_id, file_upload_id, caption)

    console.print(f"[green]✓ Image uploaded to Notion![/]")
    return file_upload_id

# ── get image from clipboard ──────────────────────────────────────────────────
def grab_clipboard_image() -> str:
    tmpfile = "/tmp/notionmind_clip.png"
    try:
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"],
            capture_output=True
        )
        if result.returncode != 0 or not result.stdout:
            return None
        with open(tmpfile, "wb") as f:
            f.write(result.stdout)
        console.print("[green]✓ Image grabbed from clipboard[/]")
        return tmpfile
    except Exception as e:
        console.print(f"[red]Clipboard grab failed: {e}[/]")
        return None
