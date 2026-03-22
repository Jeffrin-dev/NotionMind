import os
import speech_recognition as sr
from rich.console import Console

console = Console()

# ── language config ───────────────────────────────────────────────────────────
LANGUAGES = {
    "1": {"name": "English",    "edge": "en-US-JennyNeural",    "stt": "en-US", "espeak": "mb-en1"},
    "2": {"name": "Hindi",      "edge": "hi-IN-SwaraNeural",    "stt": "hi-IN", "espeak": "hi"},
    "3": {"name": "Spanish",    "edge": "es-ES-ElviraNeural",   "stt": "es-ES", "espeak": "es"},
    "4": {"name": "French",     "edge": "fr-FR-DeniseNeural",   "stt": "fr-FR", "espeak": "fr"},
    "5": {"name": "Tamil",      "edge": "ta-IN-PallaviNeural",  "stt": "ta-IN", "espeak": "ta"},
    "6": {"name": "Malayalam",  "edge": "ml-IN-SobhanaNeural",  "stt": "ml-IN", "espeak": "ml"},
}

# default language
_current_lang = LANGUAGES["1"]

# ── select language ───────────────────────────────────────────────────────────
def select_language():
    global _current_lang
    console.print("\n[bold cyan]Select Language:[/]")
    for key, lang in LANGUAGES.items():
        marker = " ◀ current" if lang == _current_lang else ""
        console.print(f"  {key}. {lang['name']}{marker}")

    from rich.prompt import Prompt
    choice = Prompt.ask("[green]Choose[/]", choices=list(LANGUAGES.keys()))
    _current_lang = LANGUAGES[choice]
    console.print(f"[green]✓ Language set to {_current_lang['name']}[/]")

def get_language() -> dict:
    return _current_lang

# ── detect internet connection ─────────────────────────────────────────────────
def is_online() -> bool:
    try:
        import httpx
        httpx.get("https://www.google.com", timeout=3)
        return True
    except:
        return False

# ── online voice: Edge TTS ────────────────────────────────────────────────────
def speak_gtts(text: str):
    try:
        import asyncio
        import edge_tts
        import pygame

        voice = _current_lang["edge"]

        async def _speak():
            tts = edge_tts.Communicate(text, voice=voice)
            tmpfile = "/tmp/notionmind_tts.mp3"
            await tts.save(tmpfile)
            return tmpfile

        tmpfile = asyncio.run(_speak())

        pygame.mixer.init()
        pygame.mixer.music.load(tmpfile)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.quit()
        try:
            os.unlink(tmpfile)
        except:
            pass

    except Exception as e:
        console.print(f"[yellow]Edge TTS failed: {e}. Falling back to espeak.[/]")
        speak_espeak(text)

# ── offline voice: espeak ─────────────────────────────────────────────────────
def speak_espeak(text: str):
    clean = (text
        .replace("*", "").replace("#", "")
        .replace("`", "").replace("[", "")
        .replace("]", "").replace("→", "")
        .replace("✓", "good").replace("•", "")
        .replace('"', "").replace("'", ""))
    voice = _current_lang["espeak"]
    os.system(f'espeak -v {voice} -s 140 -p 40 "{clean}"')

# ── smart speak ───────────────────────────────────────────────────────────────
def speak(text: str):
    clean = (text
        .replace("*", "").replace("#", "")
        .replace("`", "").replace("[", "")
        .replace("]", "").replace("→", "")
        .replace("✓", "good").replace("•", "")
        .replace('"', "").replace("'", ""))

    if is_online():
        console.print(f"[dim]🔊 Speaking ({_current_lang['name']} — Edge TTS)...[/]")
        speak_gtts(clean)
    else:
        console.print(f"[dim]🔊 Speaking ({_current_lang['name']} — espeak)...[/]")
        speak_espeak(clean)

# ── voice input ───────────────────────────────────────────────────────────────
def listen() -> str:
    recognizer = sr.Recognizer()
    lang_code = _current_lang["stt"]

    with sr.Microphone() as source:
        console.print("[dim]🎤 Adjusting for background noise...[/]")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        console.print(f"[bold green]🎤 Listening ({_current_lang['name']})... speak now![/]")

        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
            console.print("[dim]Processing...[/]")
            text = recognizer.recognize_google(audio, language=lang_code)
            console.print(f"[cyan]You said:[/] {text}")
            return text
        except sr.WaitTimeoutError:
            console.print("[yellow]No speech detected. Try again.[/]")
            return ""
        except sr.UnknownValueError:
            console.print("[yellow]Could not understand. Try again.[/]")
            return ""
        except sr.RequestError:
            console.print("[red]No internet for voice recognition.[/]")
            return ""
